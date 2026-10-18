#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "preview_resources.h"
#include "owned_decoded_texture.h"
static void owned_timer_clear(void);
#include "layer_snapshot.h"
static NFHudLayerRow owned_hud[160];static int hud_preview;static uint64_t hud_epoch=1;static unsigned hud_refresh,hud_drawn,hud_failed;
static void*owned_submission;
static const uint8_t*owned_text;
static int nf_submission_text_row(void*p,uint64_t e,unsigned r,unsigned y,uint8_t*i,uint8_t*c){if(!p||!owned_text||e!=hud_epoch||r!=hud_refresh||y>=160||!i||!c)return 0;memcpy(i,owned_text+y*240,240);memcpy(c,owned_text+38400+y*240,240);return 1;}
static int layer_read(uint64_t epoch,unsigned refresh,unsigned y,void*out,unsigned bytes){if(epoch!=hud_epoch||refresh!=hud_refresh||y>=160||bytes!=sizeof(NFHudLayerRow))return 0;memcpy(out,owned_hud+y,bytes);return 1;}
#include "live_hud_gpu.h"
/* HUD texture/program names and extension pointers belong to this context. */
static void owned_hud_context_clear(void){
 if(preview_context){
  if(hud_background)glDeleteTextures(1,&hud_background);
  void(APIENTRY*remove_program)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");
  if(remove_program){
   if(hud_program)remove_program(hud_program);
   if(obj_affine_program&&obj_affine_program!=hud_program)remove_program(obj_affine_program);
  }
 }
 hud_background=0;hud_program=0;obj_affine_program=0;
 obj_use=NULL;obj_location=NULL;obj_uniform2=NULL;obj_uniform4=NULL;
}

#include "native_geometry_view.c"
static FILE*owned_face_ledger;
static uint32_t owned_reciprocal[32768];static unsigned model_visible_faces,model_rect_rejected;
extern int nfs_model_project(const uint8_t*,const uint8_t*,unsigned,uint32_t,int32_t,int32_t,const uint32_t*,uint8_t*);
extern int nfs_model_face_visible(const uint8_t*,unsigned,const uint16_t*,unsigned,int*);
extern int nfs_model_polygon_classify(const uint8_t*,unsigned,const uint16_t*,unsigned,const int32_t*,int*);
extern int nf_road_camera_continuous(const double*,const int32_t*,double*);
extern int nf_wall_owned_quad(const uint8_t*,const uint8_t*,const int32_t*,double*);
/* Presentation matrices are borrowed for one validated call only. */
static const double*pose_camera,*pose_models,*wall_clip_override;static unsigned pose_count,pose_index,surface_clip_roads,surface_clip_models;
static int pose_world_camera(const double p[3],const int32_t*m,double*out){
 if(!pose_camera)return nf_road_camera_continuous(p,m,out);
 for(unsigned k=0;k<3;k++){out[k]=0;for(unsigned j=0;j<3;j++)out[k]+=(p[j]+pose_camera[9+j])*pose_camera[j*3+k];}return 1;
}
static int16_t pose_half(const uint8_t*p){int16_t v;memcpy(&v,p,2);return v;}
static int32_t pose_word(const uint8_t*p){int32_t v;memcpy(&v,p,4);return v;}
static int pose_wall_quad(const NFGeometryView*v,double*out){
 if(!pose_camera)return nf_wall_owned_quad(v->blocks[0],v->blocks[1],(const int32_t*)v->blocks[3],out);
 const uint8_t*s=v->blocks[0],*o=v->blocks[1];double x=(double)pose_word(s)+pose_half(o),z=(double)pose_word(s+4)+pose_half(o+2),nx=(double)pose_word(s+68)+pose_half(o+32),nz=(double)pose_word(s+72)+pose_half(o+34);
 double world[4][3]={{x,pose_half(s+8)+pose_half(o+8),z},{nx,pose_half(s+12)+pose_half(o+8),nz},{nx,pose_half(s+14)+pose_half(o+10),nz},{x,pose_half(s+10)+pose_half(o+10),z}};
 for(unsigned j=0;j<4;j++)if(!pose_world_camera(world[j],NULL,out+j*3))return 0;return 1;
}
static unsigned clip(const double in[][5],unsigned count,double out[][5]){unsigned n=0;for(unsigned i=0;i<count;i++){const double*a=in[(i+count-1)%count],*b=in[i];int ai=a[2]>=64,bi=b[2]>=64;if(ai!=bi){double t=(64-a[2])/(b[2]-a[2]);for(unsigned k=0;k<5;k++)out[n][k]=a[k]+t*(b[k]-a[k]);/* Generated intersections lie exactly on the near plane. */out[n][2]=64;n++;}if(bi){memcpy(out[n++],b,40);}}return n;}
/* Surface clip coordinates are original pixels; model right/bottom exclusive. */
static int owned_scissor(double left,double top,double right,double bottom){
 if(left<0||top<0||right>240||bottom>160||left>right||top>bottom)return 0;
 int x0=300+(int)ceil(left*13.5),x1=300+(int)ceil(right*13.5),y0=(int)ceil((160-bottom)*13.5),y1=(int)ceil((160-top)*13.5);
 glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1-x0,y1-y0);return 1;
}
static int draw_owned_road(const NFGeometryView*v){
 uint16_t bounds[4];memcpy(bounds,v->blocks[5],8);const double*sampled_clip=surface_clip_roads&&wall_clip_override?wall_clip_override+pose_index*4:NULL;
 /* Original source packets retain empty intervals after scratch updates. */
 if(!sampled_clip){if(bounds[0]>239||bounds[1]>239||bounds[2]>159||bounds[3]>159)return 0;if(bounds[0]>bounds[1]||bounds[2]>bounds[3])return 1;}
 unsigned count=gvword(v->blocks[6]);const uint8_t*mat=v->blocks[3];uint16_t shift,height;memcpy(&shift,mat+36,2);memcpy(&height,mat+38,2);height/=2;if(shift>10||!height)return 0;unsigned width=1u<<shift;
 if((size_t)width*height*2>v->sizes[7])return 0;
 double input[32][5],polygon[64][5];int16_t face_y;memcpy(&face_y,v->blocks[2]+6,2);int16_t du=(int16_t)gvword(v->blocks[6]+24),dv=(int16_t)gvword(v->blocks[6]+28);
 for(unsigned j=0;j<count;j++){const uint8_t*s=v->blocks[0]+j*68,*o=v->blocks[1]+j*32;int32_t x,z,u,w;int16_t ox,oz,y,oy;memcpy(&x,s,4);memcpy(&z,s+4,4);memcpy(&ox,o,2);memcpy(&oz,o+2,2);memcpy(&y,s+56,2);memcpy(&oy,o+6,2);memcpy(&u,s+32,4);memcpy(&w,s+36,4);double world[3]={(double)x+ox,y+oy+face_y,(double)z+oz};if(!pose_world_camera(world,(const int32_t*)v->blocks[4],input[j]))return 0;input[j][3]=u/16384.0+du/(256.0*width);input[j][4]=w/16384.0+dv/(512.0*height);}
 unsigned n=clip(input,count,polygon);if(n<3)return 1;
 GLuint texture=owned_indexed_texture(width,height,width*2,v->blocks[7],v->blocks[8],0);if(!texture)return 0;glBindTexture(GL_TEXTURE_2D,texture);if(sampled_clip){if(!owned_scissor(sampled_clip[0],sampled_clip[2],sampled_clip[1]+1,sampled_clip[3]+1))return 0;}else if(!owned_scissor(bounds[0],bounds[2],bounds[1]+1,bounds[3]+1))return 0;
 glBegin(GL_TRIANGLE_FAN);for(unsigned j=0;j<n;j++){double q=1/polygon[j][2];glTexCoord4d(polygon[j][3]*q,polygon[j][4]*q,0,q);glVertex2d(120+128*polygon[j][0]*q,87+128*polygon[j][1]*q);}glEnd();glDisable(GL_SCISSOR_TEST);return 1;
}
/* Continuous camera-space face visibility after near clipping. Bounding rejection
   is conservative: polygons spanning the viewport survive even with no inside vertex. */
__declspec(dllexport) int nf_owned_pose_face_visible_fractional(const double*points,unsigned n,double scale,double cx,double cy,const double*rect){
 if(!points||!rect||n<3||n>64||!isfinite(scale)||scale<=0)return -1;
 for(unsigned i=0;i<4;i++)if(!isfinite(rect[i]))return -1;
 double x[64],y[64],minx=1e300,maxx=-1e300,miny=1e300,maxy=-1e300;
 for(unsigned i=0;i<n;i++){const double*p=points+i*5;if(!isfinite(p[0])||!isfinite(p[1])||!isfinite(p[2])||p[2]<64)return -1;x[i]=cx+scale*p[0]/p[2];y[i]=cy+scale*p[1]/p[2];if(x[i]<minx)minx=x[i];if(x[i]>maxx)maxx=x[i];if(y[i]<miny)miny=y[i];if(y[i]>maxy)maxy=y[i];}
 double area=0;for(unsigned i=0;i<n;i++){unsigned j=(i+1)%n;area+=x[i]*y[j]-y[i]*x[j];}
 if(area>0)return 0;
 return !(maxx<rect[0]||minx>=rect[2]||maxy<rect[1]||miny>=rect[3]);
}
__declspec(dllexport) int nf_owned_pose_face_visible(const double*points,unsigned n,double scale,double cx,double cy,const int32_t*rect){
 if(!rect)return -1;double r[4]={rect[0],rect[1],rect[2],rect[3]};
 return nf_owned_pose_face_visible_fractional(points,n,scale,cx,cy,r);
}
static int draw_owned_model(const NFGeometryView*v){
 unsigned count=v->sizes[4]/6,faces=v->sizes[5],corners=v->sizes[6]/2;double camera[2048][3];if(!count||count>2048)return 0;int32_t matrix[12];memcpy(matrix,v->blocks[2],48);
 for(unsigned j=0;j<count;j++){int16_t local[3];memcpy(local,v->blocks[4]+j*6,6);for(unsigned k=0;k<3;k++)camera[j][k]=matrix[9+k]+((double)local[0]*matrix[k]+(double)local[1]*matrix[3+k]+(double)local[2]*matrix[6+k])/16384;}
 if(pose_models){const double*m=pose_models+pose_index*12;for(unsigned j=0;j<count;j++){int16_t local[3];memcpy(local,v->blocks[4]+j*6,6);for(unsigned k=0;k<3;k++)camera[j][k]=m[9+k]+local[0]*m[k]+local[1]*m[3+k]+local[2]*m[6+k];}}
 uint16_t shift,height;memcpy(&shift,v->blocks[0]+56,2);memcpy(&height,v->blocks[0]+58,2);if(shift>10||!height)return 0;unsigned width=1u<<shift;if(width*height!=v->sizes[10])return 0;
 GLuint texture=owned_indexed_texture(width,height,width,v->blocks[10],v->blocks[11],0);if(!texture)return 0;glBindTexture(GL_TEXTURE_2D,texture);unsigned offset=0;double scale=gvword(v->blocks[0]+64);int16_t center[2];memcpy(center,v->blocks[3]+8,4);
 uint8_t original_points[2048*4];if(!pose_models&&!nfs_model_project(v->blocks[2],v->blocks[4],count,(uint32_t)scale,center[0],center[1],owned_reciprocal,original_points))return 0;
 int32_t rect[4];memcpy(rect,v->blocks[9],16);double sampled_rect[4];const double*model_rect=NULL;
 if(surface_clip_models&&wall_clip_override){const double*b=wall_clip_override+pose_index*4;sampled_rect[0]=b[0];sampled_rect[1]=b[2];sampled_rect[2]=b[1];sampled_rect[3]=b[3];model_rect=sampled_rect;}
 if(model_rect){if(!owned_scissor(model_rect[0],model_rect[1],model_rect[2],model_rect[3]))return 0;}
 else if(!owned_scissor(rect[0],rect[1],rect[2],rect[3]))return 0;
 for(unsigned face=0;face<faces;face++){unsigned n=v->blocks[5][face];if(n<3||n>32||offset+n>corners)return 0;double input[32][5],polygon[64][5];uint16_t indices[32];for(unsigned j=0;j<n;j++){uint16_t vertex,uv,coords[2];memcpy(&vertex,v->blocks[6]+(offset+j)*2,2);memcpy(&uv,v->blocks[7]+(offset+j)*2,2);if(vertex>=count||uv>=v->sizes[8]/4)return 0;indices[j]=vertex;memcpy(coords,v->blocks[8]+uv*4,4);memcpy(input[j],camera[vertex],24);input[j][3]=coords[0]/32768.0;input[j][4]=coords[1]/32768.0;}offset+=n;
 unsigned clipped=clip(input,n,polygon);if(clipped<3)continue;
 if(pose_models){int visible=model_rect?nf_owned_pose_face_visible_fractional(&polygon[0][0],clipped,scale,center[0],center[1],model_rect):nf_owned_pose_face_visible(&polygon[0][0],clipped,scale,center[0],center[1],rect);if(visible<0)return 0;if(!visible)continue;}
 else{int visible,classification;if(!nfs_model_face_visible(original_points,count,indices,n,&visible)||!nfs_model_polygon_classify(original_points,count,indices,n,rect,&classification))return 0;if(!visible)continue;if(classification==4){model_rect_rejected++;continue;}}
 model_visible_faces++;
 if(owned_face_ledger){uint32_t record[3]={v->context,face,n};if(fwrite(record,4,3,owned_face_ledger)!=3||fwrite(indices,2,n,owned_face_ledger)!=n)return 0;}
 glBegin(GL_TRIANGLE_FAN);for(unsigned j=0;j<clipped;j++){double q=1/polygon[j][2];glTexCoord4d(polygon[j][3]*q,polygon[j][4]*q,0,q);glVertex2d(center[0]+scale*polygon[j][0]*q,center[1]+scale*polygon[j][1]*q);}glEnd();}
 glDisable(GL_SCISSOR_TEST);return offset==corners;
}
static uint64_t gpu_borrowed_frames;
static const uint8_t*gpu_input;static size_t gpu_input_bytes;static uint8_t*gpu_output;static DWORD gpu_owner;static int gpu_draw_only,gpu_frame_ready;static uint64_t gpu_frame_epoch;
static int reciprocal_loaded;
int main(int argc,char**argv){
 if(argc!=3&&argc!=4)return 1;FILE*f=NULL;long size;uint8_t*packet;hud_preview=0;owned_submission=NULL;owned_text=NULL;model_visible_faces=0;model_rect_rejected=0;
 if(gpu_input){size=(long)gpu_input_bytes;packet=(uint8_t*)gpu_input;gpu_borrowed_frames++;}else{f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);size=ftell(f);rewind(f);if(size<=0||size>0x1000000)return 3;packet=malloc(size);if(!packet||fread(packet,1,size,f)!=(size_t)size)return 4;fclose(f);}
 const uint8_t*geometry=packet,*background=NULL;size_t geometry_bytes=size;
 if(size>=40&&gvword(packet)==0x3346474e){unsigned refresh=gvword(packet+4),gn=gvword(packet+8),hn=gvword(packet+12),bn=gvword(packet+16),tn=gvword(packet+20);uint64_t epoch,ticks;memcpy(&epoch,packet+24,8);memcpy(&ticks,packet+32,8);
  if(argc!=3||!epoch||ticks!=(uint64_t)refresh*280896||hn!=sizeof(owned_hud)||bn!=76800||tn!=76800||(uint64_t)gn+hn+bn+tn+40!=(uint64_t)size)return 28;
  const char*expected=getenv("NF_GPU_EXPECT_EPOCH");if(expected&&strtoull(expected,NULL,10)!=epoch)return 29;
  const uint8_t*h=packet+40+gn;for(unsigned y=0;y<160;y++)if(gvword(h+y*sizeof(NFHudLayerRow))!=refresh||gvword(h+y*sizeof(NFHudLayerRow)+4)!=y)return 24;
  background=h+hn;owned_text=background+bn;for(unsigned i=0;i<38400;i++)if(background[38400+i]>1||owned_text[38400+i]>1)return 25;
  geometry=packet+40;geometry_bytes=gn;memcpy(owned_hud,h,hn);hud_preview=1;hud_refresh=refresh;hud_epoch=epoch;owned_submission=(void*)owned_text;
 }
 if(size>=20&&gvword(packet)==0x3246474e){unsigned refresh=gvword(packet+4),gn=gvword(packet+8),hn=gvword(packet+12),bn=gvword(packet+16);
  if(argc!=3||hn!=sizeof(owned_hud)||bn!=76800||(uint64_t)gn+hn+bn+20!=(uint64_t)size)return 23;
  const uint8_t*h=packet+20+gn;for(unsigned y=0;y<160;y++)if(gvword(h+y*sizeof(NFHudLayerRow))!=refresh||gvword(h+y*sizeof(NFHudLayerRow)+4)!=y)return 24;
  background=h+hn;for(unsigned i=0;i<38400;i++)if(background[38400+i]>1)return 25;
  geometry=packet+20;geometry_bytes=gn;memcpy(owned_hud,h,hn);hud_preview=1;hud_refresh=refresh;
 }
 if(size>=16&&gvword(packet)==0x3146474e){unsigned refresh=gvword(packet+4),gn=gvword(packet+8),hn=gvword(packet+12);
  if(argc!=3||hn!=sizeof(owned_hud)||(uint64_t)gn+hn+16!=(uint64_t)size)return 23;
  const uint8_t*h=packet+16+gn;for(unsigned y=0;y<160;y++)if(gvword(h+y*sizeof(NFHudLayerRow))!=refresh||gvword(h+y*sizeof(NFHudLayerRow)+4)!=y)return 24;
  geometry=packet+16;geometry_bytes=gn;memcpy(owned_hud,h,hn);hud_preview=1;hud_refresh=refresh;
 }
 NFGeometryView views[144];unsigned count=0;if(!nf_geometry_packet_views(geometry,geometry_bytes,views,144,&count))return 5;
 if(!reciprocal_loaded){FILE*table=fopen("work/camera/road-correction-reciprocal.bin","rb");if(!table)return 19;size_t loaded=fread(owned_reciprocal,4,32768,table);int closed=fclose(table);if(loaded!=32768||closed)return 19;reciprocal_loaded=1;}
 const char*ledger=getenv("NF_GPU_FACE_LEDGER");if(ledger){owned_face_ledger=fopen(ledger,"wb");if(!owned_face_ledger)return 20;}
 if(argc==4){FILE*h=fopen(argv[3],"rb");if(!h||fread(owned_hud,sizeof(owned_hud),1,h)!=1)return 21;fclose(h);hud_preview=1;hud_refresh=owned_hud[0].refresh;}
 int error=preview_context_open();if(error)return error;preview_generation++;
 glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glClearColor(.035f,.05f,.08f,1);glClear(GL_COLOR_BUFFER_BIT);glColor3f(.8f,.6f,.2f);glLineWidth(2);
 if(hud_preview){glDisable(GL_TEXTURE_2D);for(unsigned y=0;y<160;y++){uint16_t color;memcpy(&color,owned_hud[y].palette,2);unsigned r=color&31,g=(color>>5)&31,b=(color>>10)&31;glColor3ub((r<<3)|(r>>2),(g<<3)|(g>>2),(b<<3)|(b>>2));glBegin(GL_QUADS);glVertex2i(0,y);glVertex2i(240,y);glVertex2i(240,y+1);glVertex2i(0,y+1);glEnd();}}
 glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);glColor3f(1,1,1);
 if(background){uint8_t*rgba=malloc(38400*4);if(!rgba)return 26;
 for(unsigned i=0;i<38400;i++){uint16_t c;memcpy(&c,owned_hud[i/240].palette+background[i]*2,2);for(unsigned k=0;k<3;k++){unsigned v=(c>>(k*5))&31;rgba[i*4+k]=(v<<3)|(v>>2);}rgba[i*4+3]=background[38400+i]?255:0;}
 GLuint t=preview_texture(240,160,rgba);free(rgba);if(!t)return 27;glBindTexture(GL_TEXTURE_2D,t);glBegin(GL_QUADS);glTexCoord2i(0,0);glVertex2i(0,0);glTexCoord2i(1,0);glVertex2i(240,0);glTexCoord2i(1,1);glVertex2i(240,160);glTexCoord2i(0,1);glVertex2i(0,160);glEnd();}
 unsigned walls=0,roads=0,models=0;for(unsigned i=0;i<count;i++){
 pose_index=i;NFGeometryView*v=views+i;if(getenv("NF_GPU_BACKGROUND_ONLY"))continue;if(v->kind==3&&!getenv("NF_GPU_WALLS_ONLY")){if(!draw_owned_model(v))return 18;models++;continue;}if(v->kind==1&&!getenv("NF_GPU_WALLS_ONLY")){if(!draw_owned_road(v))return 17;roads++;continue;}if(v->kind!=2)continue;double camera[4][3],input[4][5],polygon[8][5];if(!pose_wall_quad(v,(double*)camera))return 6;
 const uint8_t*src=v->blocks[0],*anim=v->blocks[2],*mat=v->blocks[4];uint16_t shift,height,u0,span;int16_t au,av;uint32_t flags;int32_t vs,vspan;
 memcpy(&shift,mat+36,2);memcpy(&height,mat+38,2);memcpy(&u0,src+40,2);memcpy(&span,src+64,2);memcpy(&au,anim+4,2);memcpy(&av,anim+6,2);memcpy(&flags,v->blocks[11]+256,4);memcpy(&vs,src+16,4);memcpy(&vspan,src+24,4);
 if(shift>10||!height||height>1024||(flags&128))return 12;unsigned width=1u<<shift;if(width*height>v->sizes[8])return 13;
 double left=(double)u0/width+(double)au/(256*width),right=left+(double)span/256;if(flags&2){double t=left;left=right;right=t;}
 double top=(vs+(av>>1))/(128.0*height),bottom=top+(vspan+(av>>1))/(128.0*height);double uv[4][2]={{left,top},{right,top},{right,bottom},{left,bottom}};
 for(unsigned j=0;j<4;j++){memcpy(input[j],camera[j],24);input[j][3]=uv[j][0];input[j][4]=uv[j][1];}
 unsigned n=clip(input,4,polygon);if(n<3)continue;
 GLuint texture=owned_indexed_texture(width,height,width,v->blocks[8],v->blocks[9],1);if(!texture)return 15;glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
 uint16_t bounds[4];memcpy(bounds,v->blocks[5],8);if(bounds[0]>bounds[1]||bounds[2]>bounds[3]||bounds[1]>239||bounds[3]>159)return 16;
 const double*sampled_clip=wall_clip_override?wall_clip_override+i*4:NULL;
 if(sampled_clip){if(!owned_scissor(sampled_clip[0],sampled_clip[2],sampled_clip[1]+1,sampled_clip[3]+1))return 16;}
 else if(!owned_scissor(bounds[0],bounds[2],bounds[1]+1,bounds[3]+1))return 16;
 glBegin(GL_TRIANGLE_FAN);for(unsigned j=0;j<n;j++){double q=1/polygon[j][2];glTexCoord4d(polygon[j][3]*q,polygon[j][4]*q,0,q);glVertex2d(120+128*polygon[j][0]*q,87+128*polygon[j][1]*q);}glEnd();glDisable(GL_SCISSOR_TEST);walls++;}
 if(hud_preview){glViewport(0,0,3840,2160);if(!endpoint_hud())return 22;}
 if(gpu_draw_only){GLenum error=glGetError();if(!error){gpu_frame_ready=1;memcpy(&gpu_frame_epoch,packet+24,8);}if(!gpu_input)free(packet);return error?8:0;}
 uint8_t*pixels=malloc(3840*2160*3);if(!pixels)return 7;glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);GLenum e=glGetError();if(e)return 8;
 if(gpu_output){for(unsigned y=0;y<2160;y++)memcpy(gpu_output+y*3840*3,pixels+(2159-y)*3840*3,3840*3);}else{f=fopen(argv[2],"wb");if(!f)return 9;fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)if(fwrite(pixels+y*3840*3,1,3840*3,f)!=3840*3)return 10;fclose(f);}printf("owned_world_textured_walls=%u roads=%u models=%u native_size=3840x2160 gl_error=%u diagnostic_only=1 model_visible_faces=%u model_rect_rejected=%u\n",walls,roads,models,e,model_visible_faces,model_rect_rejected);if(owned_face_ledger)fclose(owned_face_ledger);free(pixels);if(!gpu_input)free(packet);if(!gpu_input){owned_timer_clear();owned_hud_context_clear();owned_decoded_clear();preview_shutdown();}return 0;
}

/* Synchronous renderer-thread API: context and texture cache persist; inputs
   are borrowed only for this call and RGB output is written after rendering. */
__declspec(dllexport) int nf_owned_gpu_render(const void*frame,size_t bytes,void*rgb,size_t rgb_bytes){
 if(!frame||bytes<40||bytes>0x1000000||!rgb||rgb_bytes!=3840u*2160u*3u)return 30;
 DWORD thread=GetCurrentThreadId();if(gpu_owner&&gpu_owner!=thread)return 31;gpu_owner=thread;
 gpu_input=frame;gpu_input_bytes=bytes;gpu_output=rgb;char*args[3]={"native","memory","memory"};int result=main(3,args);gpu_input=NULL;gpu_output=NULL;owned_text=NULL;owned_submission=NULL;return result;
}
__declspec(dllexport) unsigned nf_owned_gpu_contexts(void){return preview_contexts;}

extern int nf_owned_input_close(void);
__declspec(dllexport) int nf_owned_gpu_close(void){if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 0;if(!nf_owned_input_close())return 0;owned_timer_clear();owned_hud_context_clear();owned_decoded_clear();preview_shutdown();reciprocal_loaded=0;gpu_owner=0;gpu_frame_ready=0;return 1;}

/* Draw leaves completed scene in GPU target; no glReadPixels/CPU RGB copy. */
__declspec(dllexport) int nf_owned_gpu_draw(const void*frame,size_t bytes){
 if(!frame||bytes<40)return 30;uint32_t magic;memcpy(&magic,frame,4);if(magic!=0x3346474e)return 28;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 gpu_draw_only=1;gpu_frame_ready=0;uint8_t unused;int result=nf_owned_gpu_render(frame,bytes,&unused,3840u*2160u*3u);gpu_draw_only=0;return result;
}
/* Optional diagnostic readback, same renderer thread; no scene redraw. */
__declspec(dllexport) int nf_owned_gpu_read(void*out,size_t bytes){
 if(!out||bytes!=3840u*2160u*3u||!gpu_frame_ready)return 30;
 if(gpu_owner!=GetCurrentThreadId())return 31;
 uint8_t*p=malloc(bytes);if(!p)return 7;glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,p);int error=glGetError();if(!error)for(unsigned y=0;y<2160;y++)memcpy((uint8_t*)out+y*3840*3,p+(2159-y)*3840*3,3840*3);free(p);return error?8:0;
}

extern int nf_owned_input_init(HWND);
__declspec(dllexport) int nf_owned_gpu_window(unsigned show){
 if(preview_context||show>1)return 30;if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 preview_window_output=1;int error=preview_context_open();if(error)return error;gpu_owner=GetCurrentThreadId();if(!nf_owned_input_init(preview_window))return 36;if(show)ShowWindow(preview_window,SW_SHOW);return 0;
}
static uint64_t owned_present_stages[3];
static int owned_present_profile;
static uint64_t owned_present_now(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (uint64_t)(t.QuadPart*1000000000.0/f.QuadPart);}
__declspec(dllexport) int nf_owned_gpu_present_stages(uint64_t*out){if(!out||gpu_owner!=GetCurrentThreadId())return 31;memcpy(out,owned_present_stages,sizeof(owned_present_stages));return 0;}
/* Explicit diagnostic policy; current render context belongs to caller thread. */
__declspec(dllexport) int nf_owned_gpu_swap_interval(int requested,int*out){
 if(!out||gpu_owner!=GetCurrentThreadId()||!preview_context||requested< -1||requested>1)return 31;
 BOOL(WINAPI*set)(int)=(void*)wglGetProcAddress("wglSwapIntervalEXT");
 int(WINAPI*get)(void)=(void*)wglGetProcAddress("wglGetSwapIntervalEXT");
 if(!get||!set||(uintptr_t)get<=3||(uintptr_t)set<=3||(intptr_t)get==-1||(intptr_t)set==-1)return 38;
 out[0]=get();if(requested>=0&&!set(requested))return 39;out[1]=get();return requested<0||out[1]==requested?0:40;
}
/* Caller serializes epoch check with queue commit. No CPU framebuffer copy. */
__declspec(dllexport) int nf_owned_gpu_present(uint64_t epoch){
 if(gpu_owner!=GetCurrentThreadId())return 31;if(!gpu_frame_ready||!preview_window_output||epoch!=gpu_frame_epoch)return 32;
 RECT rect;if(!GetClientRect(preview_window,&rect)||rect.right<=0||rect.bottom<=0)return 33;
 void(APIENTRY*bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
 void(APIENTRY*blit)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum)=(void*)wglGetProcAddress("glBlitFramebuffer");if(!bind||!blit)return 34;
 uint64_t stage_begin=owned_present_profile?owned_present_now():0;
 glDisable(GL_SCISSOR_TEST);bind(0x8ca8,preview_fbo);bind(0x8ca9,0);blit(0,0,3840,2160,0,0,rect.right,rect.bottom,GL_COLOR_BUFFER_BIT,GL_LINEAR);
 int error=glGetError();uint64_t blit_end=owned_present_profile?owned_present_now():0;int swapped=!error&&SwapBuffers(preview_dc);uint64_t swap_end=owned_present_profile?owned_present_now():0;bind(0x8d40,preview_fbo);if(owned_present_profile){uint64_t end=owned_present_now();owned_present_stages[0]=blit_end-stage_begin;owned_present_stages[1]=swap_end-blit_end;owned_present_stages[2]=end-swap_end;}return swapped?0:35;
}

/* Diagnostic raw-pose projection hook, not a 60Hz gameplay scheduler.
   Endpoint calls use nf_owned_gpu_draw to preserve original fixed-point output. */
__declspec(dllexport) int nf_owned_gpu_draw_poses(const void*frame,size_t bytes,const double*camera,const double*models,unsigned count){
 if(!frame||bytes<40||!camera||!models||!count||count>144)return 37;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 const uint8_t*p=frame;unsigned gn=gvword(p+8);NFGeometryView views[144];unsigned actual=0;
 if(gvword(p)!=0x3346474e||gn>bytes-40||!nf_geometry_packet_views(p+40,gn,views,144,&actual)||actual!=count)return 37;
 for(unsigned i=0;i<12;i++)if(!isfinite(camera[i]))return 37;
 for(unsigned i=0;i<count*12;i++)if(!isfinite(models[i]))return 37;
 pose_camera=camera;pose_models=models;pose_count=count;int result=nf_owned_gpu_draw(frame,bytes);pose_camera=NULL;pose_models=NULL;pose_count=0;return result;
}

/* Diagnostic completion barrier. Opt-in profiling only; not a scanout fence. */
__declspec(dllexport) int nf_owned_gpu_finish(void){
 if(gpu_owner!=GetCurrentThreadId())return 31;
 if(!gpu_frame_ready)return 32;
 glFinish();return glGetError()?8:0;
}

__declspec(dllexport) uint64_t nf_owned_gpu_borrowed_frames(void){return gpu_borrowed_frames;}

/* Complete-record indexed inclusive source-pixel bounds. NULL poses retain
   endpoint projection, allowing isolated clip parity verification. */
__declspec(dllexport) int nf_owned_gpu_draw_wall_clips(const void*frame,size_t bytes,const double*camera,const double*models,const double*bounds,unsigned count){
 if(!frame||bytes<40||!bounds||!count||count>144||(!!camera!=!!models))return 37;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 const uint8_t*p=frame;unsigned gn=gvword(p+8),actual=0;NFGeometryView views[144];
 if(gvword(p)!=0x3346474e||gn>bytes-40||!nf_geometry_packet_views(p+40,gn,views,144,&actual)||actual!=count)return 37;
 for(unsigned i=0;i<count;i++)if(views[i].kind==2){const double*b=bounds+i*4;
  for(unsigned j=0;j<4;j++)if(!isfinite(b[j]))return 37;
  if(b[0]<0||b[2]<0||b[1]>239||b[3]>159||b[0]>b[1]||b[2]>b[3])return 37;
 }
 wall_clip_override=bounds;
 int result=camera?nf_owned_gpu_draw_poses(frame,bytes,camera,models,count):nf_owned_gpu_draw(frame,bytes);
 wall_clip_override=NULL;return result;
}

/* Opt-in inclusive continuous bounds for both road and wall records.
   Existing wall-only API and ordinary endpoint rendering retain their scope. */
__declspec(dllexport) int nf_owned_gpu_draw_surface_clips(const void*frame,size_t bytes,const double*camera,const double*models,const double*bounds,unsigned count){
 if(!frame||bytes<40||!bounds||!count||count>144||(!!camera!=!!models))return 37;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 const uint8_t*p=frame;unsigned gn=gvword(p+8),actual=0;NFGeometryView views[144];
 if(gvword(p)!=0x3346474e||gn>bytes-40||!nf_geometry_packet_views(p+40,gn,views,144,&actual)||actual!=count)return 37;
 for(unsigned i=0;i<count;i++)if(views[i].kind==1||views[i].kind==2){const double*b=bounds+i*4;
  for(unsigned j=0;j<4;j++)if(!isfinite(b[j]))return 37;
  if(b[0]<0||b[2]<0||b[1]>239||b[3]>159||b[0]>b[1]||b[2]>b[3])return 37;
 }
 surface_clip_roads=1;int result=nf_owned_gpu_draw_wall_clips(frame,bytes,camera,models,bounds,count);surface_clip_roads=0;return result;
}
/* Read-only context-owner counters: uploads, hits, evictions, uploaded bytes,
   resident bytes, ordinal hint hits. No GPU synchronization is introduced. */
__declspec(dllexport) int nf_owned_gpu_texture_stats(uint64_t*out){
 if(!out)return 37;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 out[0]=preview_uploads;out[1]=preview_hits;out[2]=preview_evictions;
 out[3]=preview_uploaded_bytes;out[4]=preview_texture_bytes;
 out[5]=preview_texture_hint_hits;return 0;
}

/* Opt-in diagnostic timestamp pair. Two queries only; reads never wait. */
static GLuint owned_timer_queries[2];static unsigned owned_timer_state;
static void(APIENTRY*owned_query_gen)(GLsizei,GLuint*);
static void(APIENTRY*owned_query_delete)(GLsizei,const GLuint*);
static void(APIENTRY*owned_query_counter)(GLuint,GLenum);
static void(APIENTRY*owned_query_available)(GLuint,GLenum,GLint*);
static void(APIENTRY*owned_query_result)(GLuint,GLenum,uint64_t*);
static void owned_timer_clear(void){
 if(owned_timer_queries[0]&&owned_query_delete)owned_query_delete(2,owned_timer_queries);
 memset(owned_timer_queries,0,sizeof(owned_timer_queries));owned_timer_state=0;
 owned_query_gen=NULL;owned_query_delete=NULL;owned_query_counter=NULL;owned_query_available=NULL;owned_query_result=NULL;
}
__declspec(dllexport) int nf_owned_gpu_timer_begin(void){
 if(gpu_owner!=GetCurrentThreadId())return 31;
 if(!preview_context||owned_timer_state)return 37;
 if(!owned_timer_queries[0]){
  owned_query_gen=(void*)wglGetProcAddress("glGenQueries");owned_query_delete=(void*)wglGetProcAddress("glDeleteQueries");
  owned_query_counter=(void*)wglGetProcAddress("glQueryCounter");owned_query_available=(void*)wglGetProcAddress("glGetQueryObjectiv");owned_query_result=(void*)wglGetProcAddress("glGetQueryObjectui64v");
  if(!owned_query_gen||!owned_query_delete||!owned_query_counter||!owned_query_available||!owned_query_result)return 39;
  owned_query_gen(2,owned_timer_queries);
 }
 owned_query_counter(owned_timer_queries[0],0x8e28);owned_timer_state=1;return glGetError()?8:0;
}
__declspec(dllexport) int nf_owned_gpu_timer_end(void){
 if(gpu_owner!=GetCurrentThreadId())return 31;
 if(owned_timer_state!=1)return 37;
 owned_query_counter(owned_timer_queries[1],0x8e28);owned_timer_state=2;return glGetError()?8:0;
}
__declspec(dllexport) int nf_owned_gpu_timer_read(uint64_t*out){
 if(gpu_owner!=GetCurrentThreadId())return 31;
 if(!out||owned_timer_state!=2)return 37;
 GLint ready=0;owned_query_available(owned_timer_queries[1],0x8867,&ready);if(!ready)return 38;
 uint64_t a,b;owned_query_result(owned_timer_queries[0],0x8866,&a);owned_query_result(owned_timer_queries[1],0x8866,&b);
 if(glGetError()||b<a)return 8;
 *out=b-a;owned_timer_state=0;return 0;
}


/* Model rectangles retain original exclusive right/bottom semantics. */
__declspec(dllexport) int nf_owned_gpu_draw_scene_clips(const void*frame,size_t bytes,const double*camera,const double*models,const double*bounds,unsigned count){
 if(!frame||bytes<40||!bounds||!camera||!models||!count||count>144)return 37;
 if(gpu_owner&&gpu_owner!=GetCurrentThreadId())return 31;
 const uint8_t*p=frame;unsigned gn=gvword(p+8),actual=0;NFGeometryView views[144];
 if(gvword(p)!=0x3346474e||gn>bytes-40||!nf_geometry_packet_views(p+40,gn,views,144,&actual)||actual!=count)return 37;
 for(unsigned i=0;i<count;i++)if(views[i].kind==3){const double*b=bounds+i*4;
  for(unsigned j=0;j<4;j++)if(!isfinite(b[j]))return 37;
  if(b[0]<0||b[2]<0||b[1]>240||b[3]>160||b[0]>b[1]||b[2]>b[3])return 37;
 }
 surface_clip_models=1;int result=nf_owned_gpu_draw_surface_clips(frame,bytes,camera,models,bounds,count);surface_clip_models=0;return result;
}

/* Diagnostic wall/CPU duration only: no GPU completion barrier. */
static uint64_t owned_thread_ticks(FILETIME k,FILETIME u){
 ULARGE_INTEGER a,b;a.LowPart=k.dwLowDateTime;a.HighPart=k.dwHighDateTime;
 b.LowPart=u.dwLowDateTime;b.HighPart=u.dwHighDateTime;return a.QuadPart+b.QuadPart;
}
__declspec(dllexport) int nf_owned_gpu_draw_scene_clips_timed(const void*frame,size_t bytes,const double*camera,const double*models,const double*bounds,unsigned count,uint64_t*out){
 if(!out)return 37;
 LARGE_INTEGER a,b,f;FILETIME c,e,k0,u0,k1,u1;
 int cpu0=GetThreadTimes(GetCurrentThread(),&c,&e,&k0,&u0);
 QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);
 int result=nf_owned_gpu_draw_scene_clips(frame,bytes,camera,models,bounds,count);
 QueryPerformanceCounter(&b);
 int cpu1=GetThreadTimes(GetCurrentThread(),&c,&e,&k1,&u1);
 out[0]=(uint64_t)((b.QuadPart-a.QuadPart)*1000000000.0/f.QuadPart);
 out[1]=cpu0&&cpu1?(owned_thread_ticks(k1,u1)-owned_thread_ticks(k0,u0))*100:UINT64_MAX;
 return result;
}

__declspec(dllexport) int nf_owned_gpu_present_timed(uint64_t epoch,uint64_t*out){if(!out)return 37;LARGE_INTEGER a,b,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);memset(owned_present_stages,0,sizeof(owned_present_stages));owned_present_profile=1;int result=nf_owned_gpu_present(epoch);owned_present_profile=0;QueryPerformanceCounter(&b);*out=(uint64_t)((b.QuadPart-a.QuadPart)*1000000000.0/f.QuadPart);return result;}

/* Borrowed synchronous context; no ownership retained after token commit.
   C callback invoked by handoff DLL avoids a Python callback/GIL round trip. */
typedef struct {uint64_t epoch;uint32_t timed;int32_t result;uint64_t elapsed_ns;} NFPresentContext;
__declspec(dllexport) int nf_owned_gpu_present_callback(void*context){
 NFPresentContext*c=context;if(!c||c->timed>1)return 0;
 c->elapsed_ns=0;c->result=c->timed?nf_owned_gpu_present_timed(c->epoch,&c->elapsed_ns):nf_owned_gpu_present(c->epoch);
 return c->result==0;
}
