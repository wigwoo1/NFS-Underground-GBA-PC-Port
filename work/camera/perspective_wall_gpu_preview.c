#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
typedef struct {double x,y,z,u,v;} AuditVertex;
static int audit_sample(const AuditVertex*p,double x,double y,double*uv,double*margin){
 double den=(p[1].y-p[2].y)*(p[0].x-p[2].x)+(p[2].x-p[1].x)*(p[0].y-p[2].y);
 double a=((p[1].y-p[2].y)*(x-p[2].x)+(p[2].x-p[1].x)*(y-p[2].y))/den;
 double b=((p[2].y-p[0].y)*(x-p[2].x)+(p[0].x-p[2].x)*(y-p[2].y))/den,c=1-a-b;
 *margin=fmin(a,fmin(b,c));if(*margin<0)return 0;
 double q=a/p[0].z+b/p[1].z+c/p[2].z;
 uv[0]=(a*p[0].u/p[0].z+b*p[1].u/p[1].z+c*p[2].u/p[2].z)/q;
 uv[1]=(a*p[0].v/p[0].z+b*p[1].v/p[1].z+c*p[2].v/p[2].z)/q;return 1;
}
int main(int argc,char**argv){
 if(argc!=2)return 1;FILE*f=fopen(argv[1],"rb");uint32_t h[2];AuditVertex v[4];
 if(!f||fread(h,4,2,f)!=2||!h[0]||h[0]>1024||!h[1]||h[1]>1024)return 2;
 size_t n=(size_t)h[0]*h[1];uint8_t*rgba=malloc(n*4),*states=malloc(n);
 if(!rgba||!states||fread(rgba,4,n,f)!=n||fread(states,1,n,f)!=n||fread(v,sizeof(v),1,f)!=1||fgetc(f)!=EOF)return 3;fclose(f);
 int result=preview_context_open();if(result)return result;preview_generation++;preview_zero_valid=1;
 GLuint wall=wall_zero_texture(h[0],h[1],rgba,states);if(!wall)return 4;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,240,160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glClearColor(0,1,0,1);glClear(GL_COLOR_BUFFER_BIT);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);
 if(!wall_zero_begin(wall,states))return 5;
 unsigned ids[6]={0,1,2,0,2,3};glBegin(GL_TRIANGLES);
 for(unsigned i=0;i<6;i++){AuditVertex*p=v+ids[i];double q=1/p->z;glTexCoord4d(p->u*q,p->v*q,0,q);glVertex2d(p->x,p->y);}glEnd();model_zero_end(states);
 uint8_t*pixels=malloc(3840u*2160*4);if(!pixels)return 6;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 unsigned checked=0,covered=0,boundaries=0;AuditVertex t[2][3]={{v[0],v[1],v[2]},{v[0],v[2],v[3]}};
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){
  double px=(x+.5)*240/3840,py=(2159-y+.5)*160/2160,uv[2]={0},margin[2];int inside=audit_sample(t[0],px,py,uv,margin),which=0;
  if(!inside){inside=audit_sample(t[1],px,py,uv,margin+1);which=1;}
  /* Exclude only subpixel triangle-edge neighborhoods, explicitly counted. */
  if((inside&&margin[which]<.0001)||(!inside&&(fabs(margin[0])<.0001||fabs(margin[1])<.0001))){boundaries++;continue;}
  uint8_t expected[4]={0,255,0,255};
  if(inside){covered++;double tx=uv[0]*h[0],ty=uv[1]*h[1];
   if(fabs(tx-round(tx))<.001||fabs(ty-round(ty))<.001){boundaries++;continue;}
   unsigned ix=(unsigned)((int)floor(tx)%(int)h[0]+h[0])%h[0],iy=(unsigned)((int)floor(ty)%(int)h[1]+h[1])%h[1];size_t i=(size_t)iy*h[0]+ix;
   if(states[i]==2)memcpy(expected,rgba+i*4,3);else if(states[i]!=0)return 7;
  }
  if(memcmp(pixels+((size_t)y*3840+x)*4,expected,4)){printf("mismatch x=%u y=%u inside=%d u=%.9f v=%.9f\n",x,y,inside,uv[0],uv[1]);return 8;}checked++;
 }
 printf("PASS perspective_wall_gpu checked=%u covered=%u excluded_boundary=%u\n",checked,covered,boundaries);
 free(pixels);free(states);free(rgba);preview_shutdown();return 0;
}
