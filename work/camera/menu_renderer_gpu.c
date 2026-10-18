#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "menu_renderer_gpu.h"
#include "obj_affine_gpu.h"
#include "menu_bg_gpu.h"
static unsigned half(const uint8_t*p){return p[0]|p[1]<<8;}
#include "menu_compose_gpu.h"
#include "menu_owned_source.h"
static struct {HGLRC context;GLuint program,textures[2];unsigned initializations,frames;} menu_bg;
void nf_menu_renderer_stats(unsigned out[4]){if(out){out[0]=menu_bg.initializations;out[1]=menu_bg.frames;out[2]=menu_compositor.initializations;out[3]=menu_compositor.frames;}}
void nf_menu_renderer_destroy(void){
 menu_compose_destroy();if(menu_bg.context&&menu_bg.context==wglGetCurrentContext()){glDeleteTextures(2,menu_bg.textures);void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");if(remove&&menu_bg.program)remove(menu_bg.program);}memset(&menu_bg,0,sizeof(menu_bg));
}
int nf_menu_render_hardware(const NFHardwareSubmission*submission,int compose){
 NFMenuOwnedSource source;if(!menu_owned_source(&source,submission)||!wglGetCurrentContext()||(menu_bg.context&&menu_bg.context!=wglGetCurrentContext()))return 0;
 /* Validate complete immutable source before any drawing/resource state change. */
 NFHardwareLayerRow row;
 for(unsigned y=0;y<160;y++){if(!nf_hardware_submission_row(submission,source.epoch,source.refresh,y,&row))return 0;unsigned display=half(row.registers);if((display&7)!=4||(display&0x8080)||(half(row.registers+12)&64))return 0;for(unsigned i=0;i<4;i++)if(row.affine[i]<-32768||row.affine[i]>32767)return 0;if(row.affine[4]<-134217728||row.affine[4]>134217727||row.affine[5]<-134217728||row.affine[5]>134217727)return 0;}
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");void(APIENTRY*uniformf)(GLint,GLfloat)=(void*)wglGetProcAddress("glUniform1f");if(!active||!uniform1||!uniformf)return 0;
 GLint old_program=0,old_matrix=0;glGetIntegerv(0x8b8d,&old_program);glGetIntegerv(GL_MATRIX_MODE,&old_matrix);glPushAttrib(GL_ALL_ATTRIB_BITS);glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT);glPixelStorei(GL_UNPACK_ALIGNMENT,4);glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glViewport(0,0,3840,2160);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_ALPHA_TEST);glDisable(GL_STENCIL_TEST);glDisable(GL_CULL_FACE);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glEnable(GL_SCISSOR_TEST);
 int ok=1;
 if(!menu_bg.program){if(!obj_shader_create(menu_bg_fragment))ok=0;else{menu_bg.program=obj_affine_program;menu_bg.context=wglGetCurrentContext();menu_bg.initializations++;glGenTextures(2,menu_bg.textures);for(unsigned i=0;i<2;i++){active(0x84c0+i);glBindTexture(GL_TEXTURE_2D,menu_bg.textures[i]);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,i?GL_RGBA:GL_LUMINANCE,i?256:240,i?1:160,0,i?GL_RGBA:GL_LUMINANCE,GL_UNSIGNED_BYTE,NULL);}}}
 if(ok){GLuint program=menu_bg.program;obj_use(program);uniform1(obj_location(program,"indices"),0);uniform1(obj_location(program,"palette"),1);
 for(unsigned y=0;ok&&y<160;y++){if(!nf_hardware_submission_row(submission,source.epoch,source.refresh,y,&row)){ok=0;break;}unsigned display=half(row.registers);uint8_t palette[1024];for(unsigned i=0;i<256;i++){unsigned c=half(row.palette+i*2);for(unsigned k=0;k<3;k++){unsigned b=c>>(k*5)&31;palette[i*4+k]=(b<<3)|(b>>2);}palette[i*4+3]=255;}
 active(0x84c0);glBindTexture(GL_TEXTURE_2D,menu_bg.textures[0]);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_LUMINANCE,GL_UNSIGNED_BYTE,row.vram+((display&16)?0xa000:0));active(0x84c1);glBindTexture(GL_TEXTURE_2D,menu_bg.textures[1]);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,256,1,GL_RGBA,GL_UNSIGNED_BYTE,palette);obj_uniform4(obj_location(program,"affine"),row.affine[0],row.affine[1],row.affine[2],row.affine[3]);obj_uniform2(obj_location(program,"origin"),row.affine[4],row.affine[5]);uniformf(obj_location(program,"enabled"),!!(display&0x400));int top=(int)ceil(y*13.5-.5),bottom=(int)ceil((y+1)*13.5-.5);glScissor(0,2160-bottom,3840,bottom-top);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();}
 if(ok&&compose)ok=menu_compose_gpu_read(menu_owned_row,&source);if(ok)menu_bg.frames++;}
 glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glMatrixMode(old_matrix);glPopClientAttrib();glPopAttrib();if(obj_use)obj_use(old_program);return ok&&glGetError()==GL_NO_ERROR;
}
