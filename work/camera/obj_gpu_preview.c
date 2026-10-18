#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "preview_resources.h"
#include "layer_snapshot.h"
#include "obj_tile.h"
#include "obj_affine_gpu.h"
static unsigned half(const uint8_t*p){return p[0]|((unsigned)p[1]<<8);}
int main(int argc,char**argv){
 if(argc!=3&&argc!=4)return 1;int native_affine=argc==4&&!strcmp(argv[3],"--native-affine");if(argc==4&&!native_affine)return 1;NFHardwareLayerRow*row=malloc(sizeof(*row));FILE*f=fopen(argv[1],"rb");if(!row||!f)return 2;int ok=fread(row,1,sizeof(*row),f)==sizeof(*row);fclose(f);if(!ok)return 3;unsigned display=half(row->registers);if(!(display&0x1000)||(display&0xe000))return 4;
 int error=preview_context_open();if(error)return error;preview_generation++;if(native_affine&&!obj_affine_shader())return 12;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,0.5f);glColor4f(1,1,1,1);
 unsigned drawn=0,affine=0;uint32_t image[16384];
 for(int priority=3;priority>=0;priority--)for(int i=127;i>=0;i--){unsigned a=half(row->oam+i*8),b=half(row->oam+i*8+2),c=half(row->oam+i*8+4);if(((c>>10)&3)!=(unsigned)priority||(!(a&256)&&(a&512))||(a>>14)==3||((display&7)>=3&&(c&1023)<512))continue;unsigned dimensions[2],dest[2];int16_t m[4]={0};
 if(a&4096)return 5;int decoded;if(a&256){for(unsigned j=0;j<4;j++)m[j]=(int16_t)half(row->oam+((b>>9)&31)*32+6+j*8);decoded=native_affine?nf_obj_image(row->vram,sizeof(row->vram),row->palette,sizeof(row->palette),a&~0x300u,b&~0x3000u,c,display,image,16384,dimensions):nf_obj_affine_image(row->vram,sizeof(row->vram),row->palette,sizeof(row->palette),a,b,c,display,m,image,16384,dimensions);}else decoded=nf_obj_image(row->vram,sizeof(row->vram),row->palette,sizeof(row->palette),a,b,c,display,image,16384,dimensions);if(!decoded)return 6;dest[0]=dimensions[0];dest[1]=dimensions[1];if(native_affine&&(a&256)&&(a&512)){dest[0]*=2;dest[1]*=2;}
 int x=b&511,y=a&255;if(x>=256)x-=512;if(y>=160)y-=256;if(x>=240||y>=160||x+(int)dest[0]<=0||y+(int)dest[1]<=0)continue;
 GLuint texture=preview_texture(dimensions[0],dimensions[1],(const uint8_t*)image);if(!texture)return 7;glBindTexture(GL_TEXTURE_2D,texture);double left=300+x*13.5-.01,top=y*13.5-.01,right=left+dest[0]*13.5,bottom=top+dest[1]*13.5;
 if(native_affine){obj_use((a&256)?obj_affine_program:0);if(a&256){obj_uniform4(obj_location(obj_affine_program,"inverse"),m[0],m[1],m[2],m[3]);obj_uniform2(obj_location(obj_affine_program,"origin"),300+x*13.5,y*13.5);obj_uniform2(obj_location(obj_affine_program,"sourceSize"),dimensions[0],dimensions[1]);obj_uniform2(obj_location(obj_affine_program,"destSize"),dest[0],dest[1]);}}
 glEnable(GL_SCISSOR_TEST);glScissor(300,0,3240,2160);glBegin(GL_QUADS);glTexCoord2d(0.0001/dimensions[0],0.0001/dimensions[1]);glVertex2d(left,top);glTexCoord2d(1+0.0001/dimensions[0],0.0001/dimensions[1]);glVertex2d(right,top);glTexCoord2d(1+0.0001/dimensions[0],1+0.0001/dimensions[1]);glVertex2d(right,bottom);glTexCoord2d(0.0001/dimensions[0],1+0.0001/dimensions[1]);glVertex2d(left,bottom);glEnd();drawn++;affine+=!!(a&256);
 }
 if(native_affine)obj_use(0);glDisable(GL_SCISSOR_TEST);uint8_t*rgba=malloc(3840u*2160*4);if(!rgba)return 8;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,rgba);if(glGetError()!=GL_NO_ERROR)return 9;f=fopen(argv[2],"wb");if(!f)return 10;ok=fwrite(rgba,4,3840u*2160,f)==3840u*2160;fclose(f);free(rgba);free(row);printf("drawn=%u affine=%u uploads=%u hits=%u target=3840x2160 unblended=1\n",drawn,affine,preview_uploads,preview_hits);preview_shutdown();return ok?0:11;
}

