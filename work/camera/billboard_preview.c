#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "native_surface.h"
#include "preview_resources.h"
#include "billboard_preview.h"
int main(void){
 uint8_t record[72]={0};uint32_t header[4]={0x3142464e,2,2,0};int32_t rectangle[4]={-120,-80,360,240};uint32_t uv[4]={0,0,2,2};uint16_t bounds[4]={0,240,0,160};uint8_t rgba[16]={255,0,0,255,0,255,0,255,0,0,255,255,255,255,255,0};
 memcpy(record,header,16);memcpy(record+16,rectangle,16);memcpy(record+32,uv,16);memcpy(record+48,bounds,8);memcpy(record+56,rgba,16);
 int error=preview_context_open();if(error)return error;preview_generation++;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glClearColor(0.25f,0.25f,0.25f,1);glClear(GL_COLOR_BUFFER_BIT);
 GLuint sentinel;glGenTextures(1,&sentinel);glBindTexture(GL_TEXTURE_2D,sentinel);
 GLenum hostile[]={GL_CULL_FACE,GL_SCISSOR_TEST,GL_STENCIL_TEST,GL_FOG,GL_LIGHTING,GL_COLOR_LOGIC_OP,GL_TEXTURE_GEN_S,GL_TEXTURE_GEN_T,GL_BLEND,GL_DEPTH_TEST};
 glCullFace(GL_FRONT_AND_BACK);glScissor(0,0,0,0);glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE);glPolygonMode(GL_FRONT_AND_BACK,GL_LINE);
 for(unsigned i=0;i<sizeof(hostile)/sizeof(hostile[0]);i++)glEnable(hostile[i]);
 if(draw_billboard(record,sizeof(record))!=1)return 20;glFinish();if(glGetError())return 21;
 GLint binding,mode[2];GLboolean mask[4];glGetIntegerv(GL_TEXTURE_BINDING_2D,&binding);glGetIntegerv(GL_POLYGON_MODE,mode);glGetBooleanv(GL_COLOR_WRITEMASK,mask);
 if((GLuint)binding!=sentinel||mode[0]!=GL_LINE||mode[1]!=GL_LINE||mask[0]||mask[1]||mask[2]||mask[3])return 23;
 for(unsigned i=0;i<sizeof(hostile)/sizeof(hostile[0]);i++)if(!glIsEnabled(hostile[i]))return 24;
 /* Repeat with a cache hit; draw must still preserve caller state. */
 if(draw_billboard(record,sizeof(record))!=1)return 25;
 glGetIntegerv(GL_TEXTURE_BINDING_2D,&binding);if((GLuint)binding!=sentinel||preview_hits!=1)return 26;
 const int points[4][2]={{960,1620},{2880,1620},{960,540},{2880,540}};const uint8_t expected[4][3]={{255,0,0},{0,255,0},{0,0,255},{64,64,64}};
 for(unsigned i=0;i<4;i++){uint8_t pixel[4];glReadPixels(points[i][0],points[i][1],1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);for(unsigned j=0;j<3;j++)if(abs((int)pixel[j]-expected[i][j])>1){fprintf(stderr,"pixel %u channel %u got %u\n",i,j,pixel[j]);return 22;}}
 printf("PASS: 3840x2160 clipped billboard, RGB quadrants and transparent background; uploads=%u\n",preview_uploads);glDeleteTextures(1,&sentinel);preview_shutdown();return 0;
}
