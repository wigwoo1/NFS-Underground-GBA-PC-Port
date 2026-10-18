/* Offscreen depth/alpha contract test for the experimental preview target. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define NF_DIAGNOSTIC_DEPTH
#include "preview_resources.h"
static void quad(double z,float r,float g,float b,float a){
 glColor4f(r,g,b,a);glBegin(GL_QUADS);
 glVertex3d(-1,-1,-1/z);glVertex3d(1,-1,-1/z);glVertex3d(1,1,-1/z);glVertex3d(-1,1,-1/z);glEnd();
}
static int sample(unsigned r,unsigned g,unsigned b,double z){
 unsigned char rgb[3];float depth;glFinish();glReadPixels(20,20,1,1,GL_RGB,GL_UNSIGNED_BYTE,rgb);glReadPixels(20,20,1,1,GL_DEPTH_COMPONENT,GL_FLOAT,&depth);
 return rgb[0]==r&&rgb[1]==g&&rgb[2]==b&&fabs(depth-(1/z))<2e-7;
}
int main(void){
 if(preview_context_open())return 1;
 glViewport(0,0,64,64);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(-1,1,-1,1,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 glDisable(GL_TEXTURE_2D);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_GEQUAL);glDepthMask(GL_TRUE);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);glClearDepth(0);
 unsigned passed=0;
 for(unsigned order=0;order<2;order++){
  glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
  if(order){quad(64,1,0,0,1);quad(256,0,0,1,1);}else{quad(256,0,0,1,1);quad(64,1,0,0,1);}
  if(!sample(255,0,0,64))return 2;passed++;
 }
 glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);quad(256,0,0,1,1);quad(64,1,0,0,0);quad(128,0,1,0,1);
 if(!sample(0,255,0,128))return 3;passed++;
 /* Same-depth palette replacement must pass GEQUAL, as in wall shading. */
 quad(128,1,1,0,1);if(!sample(255,255,0,128))return 4;passed++;
 if(glGetError()!=GL_NO_ERROR)return 5;
 FILE*precision=fopen("work/camera/depth-precision-tests.json","wb");if(!precision)return 6;
 fprintf(precision,"{\"scope\":\"Parallel surfaces one world unit apart, nearer drawn first; reversed float depth; far color indicates quantized tie or error\",\"samples\":[");
 const double distances[]={1,2,64,128,256,512,1024,2048,4096,8192,16384,32767,65536,1000000};unsigned collisions=0;
 for(unsigned i=0;i<sizeof(distances)/sizeof(*distances);i++){
  double z=distances[i];unsigned char rgb[3];
  glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);quad(z,1,0,0,1);quad(z+1,0,0,1,1);glFinish();glReadPixels(20,20,1,1,GL_RGB,GL_UNSIGNED_BYTE,rgb);
  int correct=rgb[0]==255&&rgb[1]==0&&rgb[2]==0;collisions+=!correct;
  fprintf(precision,"%s{\"z\":%.0f,\"near_wins\":%s}",i?",":"",z,correct?"true":"false");
 }
 fprintf(precision,"],\"collisions\":%u}\n",collisions);fclose(precision);if(collisions)return 7;
 printf("{\"result\":\"PASS\",\"checks\":%u,\"scope\":\"GPU depth ordering, alpha-discard depth preservation, equal-depth redraw and sampled depth mapping; not full wall-lighting validation\"}\n",passed);
 preview_shutdown();return 0;
}

