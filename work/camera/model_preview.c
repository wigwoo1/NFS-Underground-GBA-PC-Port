#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "rigid_motion.h"
#include "command_camera.h"
#include "preview_input.h"
#include "preview_resources.h"
#include "model_zero_gpu.h"
static double preview_alpha_override=-1;
static int preview_measure_only;
/* Worker-owned submission metadata is valid only during this render call. */
static const NFRigidPose*preview_command_cameras;
static unsigned preview_command_camera_count;
static int (*preview_before_command)(unsigned);
/* Complete adapters own their HUD and suppress legacy diagnostic callback. */
static int preview_skip_diagnostic_hud;
static int (*preview_after_commands)(void);
static int (*preview_after_background)(void);
static int (*preview_after_command)(unsigned);
static int preview_command_camera(unsigned command,NFRigidPose poses[4]){
 return nf_command_camera_apply(preview_command_cameras,preview_command_camera_count,command,poses);
}
#include "road_preview.h"
#if defined(NF_DIAGNOSTIC_DEPTH) && defined(NF_SOURCE_COMMAND_ORDER)
#include "source_command_depth.h"
#endif
/* Packet-owned additional models use the same pose, clipping and texture path. */
static PreviewMemory preview_extra_models[15];
static unsigned preview_extra_count;
static int draw_extra_model(unsigned index,double alpha,unsigned command){
 if(index>=preview_extra_count)return 0;
 const uint8_t*m=preview_extra_models[index].data;uint32_t h[6];double projection[3];NFRigidPose poses[4];
 memcpy(h,m,24);memcpy(projection,m+24,24);memcpy(poses,m+48,224);if(!preview_command_camera(command,poses))return 0;
 NFPoint3 vertices[2048],points[2048];memcpy(vertices,m+272,h[1]*24);
 if(!nf_rigid_scene_sample(poses,poses+1,poses+2,poses+3,alpha,vertices,h[1],points))return 0;
 const uint8_t*sizes=m+272+h[1]*24,*ids=sizes+h[2],*uv=ids+h[3]*2,*texture=uv+h[3]*16;
 const uint8_t*indices=preview_model_indices[index+1];GLuint skin=model_zero_texture(h[4],h[5],texture,indices);if(!skin||!model_zero_begin(skin,indices))return 0;
 unsigned offset=0;
 for(unsigned face=0;face<h[2];face++){
  unsigned original=sizes[face];RoadVertex in[32],out[64];double x[64],y[64],q[64];
  for(unsigned i=0;i<original;i++){uint16_t id;double coords[2];memcpy(&id,ids+(offset+i)*2,2);memcpy(coords,uv+(offset+i)*16,16);in[i]=(RoadVertex){points[id],coords[0],coords[1]};}
  unsigned n=texture_near_clip(in,original,out,1);double area=0;
  for(unsigned i=0;i<n;i++){q[i]=1/out[i].p.z;x[i]=projection[0]+projection[2]*out[i].p.x*q[i];y[i]=projection[1]+projection[2]*out[i].p.y*q[i];}
  for(unsigned i=0;i<n;i++)area+=x[i]*y[(i+1)%n]-x[(i+1)%n]*y[i];
  if(n>=3&&area<0){glBegin(GL_TRIANGLE_FAN);for(unsigned i=0;i<n;i++){glTexCoord4d(out[i].u*q[i],out[i].v*q[i],0,q[i]);
#ifdef NF_DIAGNOSTIC_DEPTH
   glVertex3d(x[i],y[i],-q[i]);
#else
   glVertex2d(x[i],y[i]);
#endif
  }glEnd();}offset+=original;
 }model_zero_end(indices);return 1;
}
typedef struct {unsigned kind,count;NFPoint3 vertices[32];} WorldRing;
/* Clip candidate wireframe rings in camera space before dividing by depth. */
static unsigned near_clip(const NFPoint3*in,unsigned count,NFPoint3*out){
 unsigned n=0;
 for(unsigned i=0;i<count;i++){
  NFPoint3 a=in[(i+count-1)%count],b=in[i];int ai=a.z>=64,bi=b.z>=64;
  if(ai!=bi){double t=(64-a.z)/(b.z-a.z);out[n++]=(NFPoint3){a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,64};}
  if(bi)out[n++]=b;
 }return n;
}
int main(int argc,char**argv){
#ifdef NF_DIAGNOSTIC_RENDER_STAGE
 NF_DIAGNOSTIC_RENDER_STAGE(0);
#endif
 if(argc<3||argc>7)return 1;
 WorldRing world[512];unsigned world_count=0;
 if(argc>=4){PreviewInput*w=preview_input(1,argv[3]);uint32_t header[2];if(!w||!read_bytes(w,header,8)||header[0]!=0x31574650||header[1]>512)return 16;
  world_count=header[1];for(unsigned i=0;i<world_count;i++){uint32_t info[2];if(!read_bytes(w,info,8)||info[1]<3||info[1]>32)return 16;world[i].kind=info[0];world[i].count=info[1];if(!read_bytes(w,world[i].vertices,info[1]*sizeof(NFPoint3)))return 16;}preview_close(w);
 }
 PreviewInput*f=preview_input(0,argv[1]);if(!f)return 2;
 uint32_t h[6];double projection[3];NFRigidPose poses[4];
 if(!read_bytes(f,h,sizeof(h))||h[0]!=0x314d464e||h[1]>2048||h[2]>512||h[3]>4096||h[4]>1024||h[5]>1024)return 3;
 if(!read_bytes(f,projection,sizeof(projection))||!read_bytes(f,poses,sizeof(poses)))return 4;
 NFPoint3*model=calloc(h[1],sizeof(*model)),*points=calloc(h[1],sizeof(*points));
 uint8_t*sizes=malloc(h[2]);uint16_t*ids=malloc(h[3]*2);double*uv=malloc(h[3]*2*sizeof(double));uint8_t*texture=malloc(h[4]*h[5]*4);
 if(!model||!points||!sizes||!ids||!uv||!texture)return 5;
 if(!read_bytes(f,model,h[1]*sizeof(*model))||!read_bytes(f,sizes,h[2])||!read_bytes(f,ids,h[3]*2)||!read_bytes(f,uv,h[3]*2*sizeof(double))||!read_bytes(f,texture,h[4]*h[5]*4))return 6;
 preview_close(f);unsigned total=0;for(unsigned i=0;i<h[2];i++){if(sizes[i]<3||sizes[i]>32)return 7;total+=sizes[i];}if(total!=h[3])return 7;
 for(unsigned i=0;i<h[3];i++)if(ids[i]>=h[1])return 7;
 int context_error=preview_context_open();if(context_error)return context_error;preview_generation++;
 GLuint skin=model_zero_texture(h[4],h[5],texture,preview_model_indices[0]);if(!skin)return 26;
 glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glEnable(GL_TEXTURE_2D);glClearColor(.035f,.05f,.08f,1);glPixelStorei(GL_PACK_ALIGNMENT,1);
 glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);
 if(argc>=5&&!load_roads(argv[4]))return 18;
 uint32_t order[144],order_count=0;
 if(argc>=6){PreviewInput*o=preview_input(3,argv[5]);uint32_t header[2];if(!o||!read_bytes(o,header,8)||header[0]!=0x314f464e||header[1]!=road_count+1+preview_extra_count||header[1]>144)return 19;
  order_count=header[1];if(!read_bytes(o,order,order_count*4))return 19;preview_close(o);
  if(preview_command_cameras&&preview_command_camera_count!=order_count)return 19;
  unsigned seen[144]={0};for(unsigned i=0;i<order_count;i++){unsigned index=order[i]>=UINT32_MAX-15?road_count+UINT32_MAX-order[i]:order[i];if(index>=road_count+1+preview_extra_count||seen[index]++)return 19;}
 }
 if(argc==7&&!load_wall_lighting(argv[6]))return 20;
 uint8_t*pixels=preview_measure_only?NULL:malloc(3840*2160*3);if(!preview_measure_only&&!pixels)return 12;
 unsigned first_phase=0,last_phase=5;const char*phase_env=getenv("NF_PREVIEW_PHASE");
 if(phase_env){char*end;long phase=strtol(phase_env,&end,10);if(!*phase_env||*end||phase<0||phase>4)return 21;first_phase=(unsigned)phase;last_phase=first_phase+1;}
#ifdef NF_DIAGNOSTIC_RENDER_STAGE
 NF_DIAGNOSTIC_RENDER_STAGE(1);
#endif
 for(unsigned frame=first_phase;frame<last_phase;frame++){
  double alpha=preview_alpha_override>=0?preview_alpha_override:frame/4.;
  if(!nf_rigid_scene_sample(poses,poses+1,poses+2,poses+3,alpha,model,h[1],points))return 13;
  #ifdef NF_DIAGNOSTIC_DEPTH
  glEnable(GL_DEPTH_TEST);glDepthFunc(GL_GEQUAL);glDepthMask(GL_TRUE);glClearDepth(0);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
#else
  glClear(GL_COLOR_BUFFER_BIT);
#endif
  if(!model_zero_background_draw())return 40;
  if(preview_after_background&&!preview_after_background())return 48;
  unsigned offset=0,drawn=0;
  if(!order_count&&!draw_road_range(poses,alpha,projection,0,road_count))return 42;
  NFRigidPose fixed={{0,0,0},{0,0,0,1}};
  glDisable(GL_TEXTURE_2D);glLineWidth(2);
  for(unsigned ring=0;ring<world_count;ring++){
   NFPoint3 camera_points[32],clipped[64];
   if(!nf_rigid_scene_sample(poses,poses+1,&fixed,&fixed,alpha,world[ring].vertices,world[ring].count,camera_points))return 17;
   unsigned n=near_clip(camera_points,world[ring].count,clipped);if(n<3)continue;
   if(world[ring].kind==1)glColor3f(.1f,.7f,.9f);else glColor3f(.65f,.45f,.2f);
   glBegin(GL_LINE_LOOP);for(unsigned i=0;i<n;i++)glVertex2d(projection[0]+projection[2]*clipped[i].x/clipped[i].z,projection[1]+projection[2]*clipped[i].y/clipped[i].z);glEnd();
  }
  glColor3f(1,1,1);glEnable(GL_TEXTURE_2D);
  for(unsigned command=0;command<(order_count?order_count:1);command++){
   if(preview_before_command&&!preview_before_command(command))return 44;
#ifdef NF_DIAGNOSTIC_COMMAND_FILTER
   if(order_count&&!NF_DIAGNOSTIC_COMMAND_FILTER(order[command]))continue;
#endif
#ifdef NF_DIAGNOSTIC_MODEL_CLIP
   NF_DIAGNOSTIC_MODEL_CLIP(-1);
#endif
#if defined(NF_DIAGNOSTIC_DEPTH) && defined(NF_SOURCE_COMMAND_ORDER)
   preview_source_depth_command(order_count?order[command]:UINT32_MAX);
#endif
#ifdef NF_DIAGNOSTIC_MODEL_CLIP
   if(!order_count||order[command]>=UINT32_MAX-15)NF_DIAGNOSTIC_MODEL_CLIP(order_count?(int)(UINT32_MAX-order[command]):0);
#endif
   if(order_count&&order[command]>=UINT32_MAX-15&&order[command]!=UINT32_MAX){if(!draw_extra_model(UINT32_MAX-order[command]-1,alpha,command))return 36;if(preview_after_command&&!preview_after_command(command))return 44;continue;}
   NFRigidPose command_poses[4];memcpy(command_poses,poses,sizeof(command_poses));if(!preview_command_camera(command,command_poses))return 43;
   if(order_count&&order[command]!=0xffffffff){if(!draw_road_range(command_poses,alpha,projection,order[command],order[command]+1))return 42;if(preview_after_command&&!preview_after_command(command))return 44;continue;}
   if(preview_command_cameras&&!nf_rigid_scene_sample(command_poses,command_poses+1,command_poses+2,command_poses+3,alpha,model,h[1],points))return 43;
   if(!model_zero_begin(skin,preview_model_indices[0]))return 37;offset=0;
  for(unsigned face=0;face<h[2];face++){
   unsigned original_n=sizes[face];RoadVertex in[32],out[64];double x[64],y[64],q[64];
   for(unsigned i=0;i<original_n;i++)in[i]=(RoadVertex){points[ids[offset+i]],uv[(offset+i)*2],uv[(offset+i)*2+1]};
   unsigned n=texture_near_clip(in,original_n,out,1);double area=0;
   for(unsigned i=0;i<n;i++){q[i]=1/out[i].p.z;x[i]=projection[0]+projection[2]*out[i].p.x*q[i];y[i]=projection[1]+projection[2]*out[i].p.y*q[i];}
   for(unsigned i=0;i<n;i++)area+=x[i]*y[(i+1)%n]-x[(i+1)%n]*y[i];
   if(n>=3&&area<0){
    glBegin(GL_TRIANGLE_FAN);for(unsigned i=0;i<n;i++){glTexCoord4d(out[i].u*q[i],out[i].v*q[i],0,q[i]);
#ifdef NF_DIAGNOSTIC_DEPTH
    glVertex3d(x[i],y[i],-q[i]);
#else
    glVertex2d(x[i],y[i]);
#endif
}glEnd();drawn++;
   }offset+=original_n;
  }
  model_zero_end(preview_model_indices[0]);
  if(preview_after_command&&!preview_after_command(command))return 44;
  }
  if(preview_after_commands&&!preview_after_commands())return 44;
#if defined(NF_DIAGNOSTIC_DEPTH) && defined(NF_SOURCE_COMMAND_ORDER)
  preview_source_depth_end();
#endif
#ifdef NF_DIAGNOSTIC_MODEL_CLIP
  NF_DIAGNOSTIC_MODEL_CLIP(-1);
#endif
#ifdef NF_DIAGNOSTIC_RENDER_STAGE
  NF_DIAGNOSTIC_RENDER_STAGE(2);
#endif
#ifdef NF_DIAGNOSTIC_HUD_DRAW
  if(!preview_skip_diagnostic_hud&&!NF_DIAGNOSTIC_HUD_DRAW())return 35;
#endif
#ifdef NF_DIAGNOSTIC_RENDER_STAGE
  NF_DIAGNOSTIC_RENDER_STAGE(3);
#endif
  LARGE_INTEGER finish_begin,finish_end,finish_frequency;QueryPerformanceFrequency(&finish_frequency);QueryPerformanceCounter(&finish_begin);
  if(getenv("NF_TEST_ASYNC_RENDER_FINISH"))glFlush();else glFinish();
  QueryPerformanceCounter(&finish_end);preview_finish_wall_ms+=(finish_end.QuadPart-finish_begin.QuadPart)*1000.0/finish_frequency.QuadPart;preview_finish_calls++;
  if(glGetError()!=GL_NO_ERROR)return 14;
#ifdef NF_DIAGNOSTIC_RENDER_STAGE
  NF_DIAGNOSTIC_RENDER_STAGE(4);
#endif
  if(!preview_measure_only){
  glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,pixels);
  char path[1024];snprintf(path,sizeof(path),"%s-%u.ppm",argv[2],frame);FILE*output=fopen(path,"wb");if(!output)return 15;fprintf(output,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(pixels+y*3840*3,3,3840,output);fclose(output);
  printf("frame=%u phase=%.2f faces=%u lit=%u lighting_fallback=%u\n",frame,alpha,drawn,lighting_applied,lighting_fallback);
  }
 }
 if(!preview_keep_context)preview_shutdown();
 free(model);free(points);free(sizes);free(ids);free(uv);free(texture);free(pixels);return 0;
}

