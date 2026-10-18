#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "scene.h"
#include "gpu.h"
#define FB 0x8D40
#define ATTACHMENT 0x8CE0
#define COMPLETE 0x8CD5
static void(APIENTRY* GenFramebuffers)(GLsizei,GLuint*);
static void(APIENTRY* BindFramebuffer)(GLenum,GLuint);
static void(APIENTRY* FramebufferTexture2D)(GLenum,GLenum,GLenum,GLuint,GLint);
static GLenum(APIENTRY* CheckFramebufferStatus)(GLenum);
static void(APIENTRY* DeleteFramebuffers)(GLsizei,const GLuint*);
static GLuint fbo,target,reference,overlay;
static uint32_t texture_pixels[1024*1024],overlay_pixels[240*160];
static int poly_count;
static uint32_t palette_hash;
typedef struct {NFPoly spec;GLuint gl;unsigned refreshed;} CachedTexture;
static CachedTexture cache[256];static unsigned cache_count;
static unsigned draw_serial;
void* nf_pixels(void);unsigned nf_read(unsigned,int);
static void setup_texture(GLuint id,int w,int h,const void* bytes,int filter){
 glBindTexture(GL_TEXTURE_2D,id);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,filter);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,filter);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,bytes);
}
int nf_gpu_init(void){
 GenFramebuffers=(void*)wglGetProcAddress("glGenFramebuffers");BindFramebuffer=(void*)wglGetProcAddress("glBindFramebuffer");FramebufferTexture2D=(void*)wglGetProcAddress("glFramebufferTexture2D");CheckFramebufferStatus=(void*)wglGetProcAddress("glCheckFramebufferStatus");DeleteFramebuffers=(void*)wglGetProcAddress("glDeleteFramebuffers");
 if(!GenFramebuffers||!BindFramebuffer||!FramebufferTexture2D||!CheckFramebufferStatus||!DeleteFramebuffers)return 0;
 glGenTextures(1,&target);setup_texture(target,3840,2160,NULL,GL_LINEAR);GenFramebuffers(1,&fbo);BindFramebuffer(FB,fbo);FramebufferTexture2D(FB,ATTACHMENT,GL_TEXTURE_2D,target,0);
 int ok=CheckFramebufferStatus(FB)==COMPLETE;BindFramebuffer(FB,0);
 glGenTextures(1,&reference);setup_texture(reference,240,160,NULL,GL_NEAREST);glGenTextures(1,&overlay);setup_texture(overlay,240,160,NULL,GL_NEAREST);
 return ok;
}
static void projection(float w,float h){glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,w,h,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();}
static void quad(GLuint id,int invert){
 glBindTexture(GL_TEXTURE_2D,id);glColor4f(1,1,1,1);glBegin(GL_QUADS);glTexCoord2f(0,invert?1:0);glVertex2f(0,0);glTexCoord2f(1,invert?1:0);glVertex2f(240,0);glTexCoord2f(1,invert?0:1);glVertex2f(240,160);glTexCoord2f(0,invert?0:1);glVertex2f(0,160);glEnd();
}
static GLuint texture_for(const NFPoly* p){
 unsigned i;for(i=0;i<cache_count;i++){NFPoly* s=&cache[i].spec;if(s->address==p->address&&s->width==p->width&&s->height==p->height&&s->stride==p->stride&&s->shade==p->shade&&s->kind==p->kind)break;}
 if(i==cache_count){if(cache_count==256)return 0;if(!nf_texture(p,texture_pixels))return 0;cache[i].spec=*p;glGenTextures(1,&cache[i].gl);setup_texture(cache[i].gl,p->width,p->height,texture_pixels,GL_NEAREST);cache_count++;}
 /* RAM-backed car skins can change without a new ROM address. */
 else if(p->address<0x08000000&&cache[i].refreshed!=draw_serial){if(!nf_texture(p,texture_pixels))return 0;glBindTexture(GL_TEXTURE_2D,cache[i].gl);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,p->width,p->height,GL_RGBA,GL_UNSIGNED_BYTE,texture_pixels);}
 cache[i].refreshed=draw_serial;
 return cache[i].gl;
}
static float cross(const NFVertex* a,const NFVertex* b,const NFVertex* c){return (b->x-a->x)*(c->y-a->y)-(b->y-a->y)*(c->x-a->x);}
static void vertex(const NFVertex* v){glTexCoord4f(v->s,v->t,0,v->q);glVertex2f(v->x,v->y);}
static void polygon(const NFPoly* p){
 int ids[32],n=0;float area=0;
 for(unsigned i=0;i<p->count;i++){
  const NFVertex* v=&p->v[i];if(!isfinite(v->x)||!isfinite(v->y)||!isfinite(v->s)||!isfinite(v->t)||!isfinite(v->q)||v->q<=0)return;
  if(n&&fabsf(v->x-p->v[ids[n-1]].x)<0.001f&&fabsf(v->y-p->v[ids[n-1]].y)<0.001f)continue;ids[n++]=i;
 }
 if(n>2&&p->v[ids[0]].x==p->v[ids[n-1]].x&&p->v[ids[0]].y==p->v[ids[n-1]].y)n--;
 for(int i=0;i<n;i++){const NFVertex*a=&p->v[ids[i]],*b=&p->v[ids[(i+1)%n]];area+=a->x*b->y-b->x*a->y;}
 if(fabsf(area)<.01f)return;float sign=area>0?1:-1;
 GLuint tex=texture_for(p);if(!tex)return;glBindTexture(GL_TEXTURE_2D,tex);glBegin(GL_TRIANGLES);
 while(n>=3){int found=0;
  for(int i=0;i<n;i++){
   int prev=(i+n-1)%n,next=(i+1)%n;const NFVertex *a=&p->v[ids[prev]],*b=&p->v[ids[i]],*c=&p->v[ids[next]];
   float cr=cross(a,b,c)*sign;if(cr<.001f)continue;int inside=0;
   for(int j=0;j<n;j++){if(j==prev||j==i||j==next)continue;const NFVertex*v=&p->v[ids[j]];if(cross(a,b,v)*sign>0.001f&&cross(b,c,v)*sign>0.001f&&cross(c,a,v)*sign>0.001f){inside=1;break;}}
   if(inside)continue;vertex(a);vertex(b);vertex(c);memmove(ids+i,ids+i+1,(n-i-1)*sizeof(int));n--;found=1;break;
  }
  if(!found)break;
 }
 glEnd();
}
void nf_gpu_draw(int w,int h,int native_view){
 draw_serial++;
 unsigned hash=2166136261u;for(int i=0;i<256;i++)hash=(hash^nf_read(0x05000000+i*2,2))*16777619u;
 if(hash!=palette_hash){for(unsigned i=0;i<cache_count;i++)glDeleteTextures(1,&cache[i].gl);cache_count=0;palette_hash=hash;}
 glEnable(GL_TEXTURE_2D);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glColor4f(1,1,1,1);
 glBindTexture(GL_TEXTURE_2D,reference);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,nf_pixels());
 BindFramebuffer(FB,fbo);glViewport(0,0,3840,2160);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);glViewport(300,0,3240,2160);projection(240,160);quad(reference,0);
 const NFPoly* polys=nf_scene(&poly_count);
 if(native_view && (nf_read(0x04000000,2)&7)==4 && poly_count>0){
  glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,0.5f);
  for(int i=0;i<poly_count;i++)polygon(&polys[i]);
  glDisable(GL_ALPHA_TEST);
  nf_overlay(overlay_pixels);glBindTexture(GL_TEXTURE_2D,overlay);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,overlay_pixels);
  glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);quad(overlay,0);glDisable(GL_BLEND);
 }
 BindFramebuffer(FB,0);glViewport(0,0,w,h);glClear(GL_COLOR_BUFFER_BIT);
 int vw=w,vh=w*2160/3840;if(vh>h){vh=h;vw=h*3840/2160;}glViewport((w-vw)/2,(h-vh)/2,vw,vh);projection(240,160);quad(target,1);
}
int nf_gpu_capture(const char* path){
 uint8_t* rgb=malloc(3840*2160*3);if(!rgb)return 0;
 BindFramebuffer(FB,fbo);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,rgb);BindFramebuffer(FB,0);
 FILE*f=fopen(path,"wb");if(!f){free(rgb);return 0;}fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(rgb+y*3840*3,3,3840,f);fclose(f);free(rgb);return 1;
}
int nf_gpu_polygon_count(void){return poly_count;}
void nf_gpu_close(void){for(unsigned i=0;i<cache_count;i++)glDeleteTextures(1,&cache[i].gl);cache_count=0;if(fbo)DeleteFramebuffers(1,&fbo);glDeleteTextures(1,&target);glDeleteTextures(1,&reference);glDeleteTextures(1,&overlay);}

unsigned nf_gpu_frame_hash(void){
 static unsigned pixels[1000*600];unsigned hash=2166136261u;
 BindFramebuffer(FB,fbo);glReadPixels(1200,600,1000,600,GL_RGBA,GL_UNSIGNED_BYTE,pixels);BindFramebuffer(FB,0);
 for(unsigned i=0;i<1000*600;i++)hash=(hash^pixels[i])*16777619u;
 return hash;
}
