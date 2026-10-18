#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "preview_resources.h"
#include "obj_affine_gpu.h"
#include "obj_effect_gpu.h"
#include "obj_textured_effect_gpu.h"
static void color_uniform(const char*name,uint32_t color){obj_uniform4(obj_location(obj_affine_program,name),color&255,(color>>8)&255,(color>>16)&255,color?1:0);}
int main(int argc,char**argv){if(argc!=3&&argc!=4)return 1;int textured=argc==4&&!strcmp(argv[3],"--textured");if(argc==4&&!textured)return 1;FILE*f=fopen(argv[1],"rb");if(!f)return 2;uint32_t input[1024][8];if(fread(input,sizeof(input),1,f)!=1){fclose(f);return 3;}fclose(f);int error=preview_context_open();if(error)return error;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);GLuint background=0,sprite=0;void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");
 if(textured){if(!active||!uniform1)return 13;const char*gradient="#version 120\nvoid main(){vec2 p=floor(gl_FragCoord.xy);gl_FragColor=vec4(mod(p.x,256.0),mod(p.y,256.0),mod(floor(p.x/16.0)+floor(p.y/16.0),256.0),255.0)/255.0;}";if(!obj_shader_create(gradient))return 12;obj_use(obj_affine_program);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();obj_use(0);glGenTextures(1,&background);glBindTexture(GL_TEXTURE_2D,background);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,3840,2160,0);glGenTextures(1,&sprite);}
 if(!obj_shader_create(textured?obj_textured_effect_fragment:obj_effect_fragment))return 12;obj_use(obj_affine_program);
 if(textured){uniform1(obj_location(obj_affine_program,"nativeBackground"),1);active(0x84c1);glBindTexture(GL_TEXTURE_2D,background);active(0x84c0);uniform1(obj_location(obj_affine_program,"spriteAsset"),0);}
 for(unsigned i=0;i<1024;i++){uint32_t*a=input[i];unsigned blend=a[5],alpha=a[6],y=a[7],ea=alpha&31,eb=(alpha>>8)&31,ey=y&31;if(ea>16)ea=16;if(eb>16)eb=16;if(ey>16)ey=16;color_uniform("objectColor",a[0]);color_uniform("backgroundColor",a[2]);color_uniform("backdropColor",a[4]);obj_uniform4(obj_location(obj_affine_program,"parameters"),(blend>>6)&3,(a[1]>>2)&3,a[1]&3,a[3]);obj_uniform4(obj_location(obj_affine_program,"firstTargets"),!!(blend&16),!!(blend&4),!!(blend&32),0);obj_uniform4(obj_location(obj_affine_program,"secondTargets"),!!(blend&4096),!!(blend&1024),!!(blend&8192),0);obj_uniform4(obj_location(obj_affine_program,"coefficients"),ea,eb,ey,0);unsigned x=(i%60)*64,z=(i/60)*120;if(textured){uint32_t pixels[64];for(unsigned t=0;t<64;t++)pixels[t]=((t%8+t/8)%3==0)?0:a[0];glBindTexture(GL_TEXTURE_2D,sprite);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);obj_uniform4(obj_location(obj_affine_program,"sourceRectangle"),x,z,64,120);}glBegin(GL_QUADS);glVertex2i(x,z);glVertex2i(x+64,z);glVertex2i(x+64,z+120);glVertex2i(x,z+120);glEnd();}
 obj_use(0);uint8_t*rgba=malloc(3840u*2160*4);if(!rgba)return 8;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,rgba);if(glGetError()!=GL_NO_ERROR)return 9;f=fopen(argv[2],"wb");if(!f)return 10;int ok=fwrite(rgba,4,3840u*2160,f)==3840u*2160;fclose(f);free(rgba);printf("cases=1024 target=3840x2160 gpu_effects=1\n");preview_shutdown();return ok?0:11;}
