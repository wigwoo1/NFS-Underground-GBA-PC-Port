/* Actual GL fragment lookup of every index/row, including index0.
   Diagnostic only; does not render captured original 3D pixels. */
#define NF_PACKET_NO_MAIN
#include "packet_preview.c"
#include "display_palette_gpu.h"
static uint16_t palette[160][256];
int main(int argc,char**argv){
 if(argc>2)return 39;
 if(argc==2){FILE*input=fopen(argv[1],"rb");if(!input)return 38;int valid=fread(palette,1,sizeof(palette),input)==sizeof(palette)&&fgetc(input)==EOF;fclose(input);if(!valid)return 37;}
 int result=preview_context_open();if(result)return result;
 GLuint(APIENTRY*create)(GLenum)=(void*)wglGetProcAddress("glCreateShader");
 void(APIENTRY*source)(GLuint,GLsizei,const char*const*,const GLint*)=(void*)wglGetProcAddress("glShaderSource");
 void(APIENTRY*compile)(GLuint)=(void*)wglGetProcAddress("glCompileShader");
 void(APIENTRY*get)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetShaderiv");
 GLuint(APIENTRY*program)(void)=(void*)wglGetProcAddress("glCreateProgram");
 void(APIENTRY*attach)(GLuint,GLuint)=(void*)wglGetProcAddress("glAttachShader");
 void(APIENTRY*link)(GLuint)=(void*)wglGetProcAddress("glLinkProgram");
 void(APIENTRY*check)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetProgramiv");
 if(!model_zero_shader()||!create||!source||!compile||!get||!program||!attach||!link||!check)return 40;
 const char*vs="#version 120\nvoid main(){gl_Position=gl_Vertex;}";
 const char*fs="#version 120\nuniform sampler2D palette;void main(){float index=floor(gl_FragCoord.x);float row=floor(gl_FragCoord.y);gl_FragColor=texture2D(palette,vec2((index+0.5)/256.0,(row+0.5)/160.0));}";
 GLuint v=create(0x8b31),f=create(0x8b30);source(v,1,&vs,NULL);source(f,1,&fs,NULL);compile(v);compile(f);GLint ok=0;
 get(v,0x8b81,&ok);if(!ok)return 41;get(f,0x8b81,&ok);if(!ok)return 42;
 GLuint shader=program();attach(shader,v);attach(shader,f);link(shader);check(shader,0x8b82,&ok);if(!ok)return 43;
 uint8_t*readback=malloc(256u*160u*4u);if(!readback)return 44;
 glViewport(0,0,256,160);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_ALPHA_TEST);glDisable(GL_DITHER);
 unsigned phases=argc==2?1:4;
 for(unsigned phase=0;phase<phases;phase++){
  preview_generation++;if(argc==1)for(unsigned y=0;y<160;y++)for(unsigned i=0;i<256;i++)palette[y][i]=(uint16_t)((i*131+y*997+phase*2371)&32767);
  GLuint texture=display_palette_texture(palette);if(!texture)return 45;
  model_zero_active(0x84c0);glBindTexture(GL_TEXTURE_2D,texture);model_zero_use(shader);model_zero_uniform(model_zero_location(shader,"palette"),0);
  glBegin(GL_QUADS);glVertex2f(-1,-1);glVertex2f(1,-1);glVertex2f(1,1);glVertex2f(-1,1);glEnd();
  glReadPixels(0,0,256,160,GL_RGBA,GL_UNSIGNED_BYTE,readback);
  if(glGetError()!=GL_NO_ERROR)return 46;
  for(unsigned y=0;y<160;y++)for(unsigned i=0;i<256;i++)for(unsigned k=0;k<4;k++){
   unsigned expected=k==3?255:((palette[y][i]>>(k*5))&31)*255/31;
   if(readback[(y*256+i)*4+k]!=expected){printf("mismatch phase=%u row=%u index=%u channel=%u\n",phase,y,i,k);return 47;}
  }
 }
 model_zero_use(0);free(readback);preview_shutdown();printf("PASS display_palette_gpu phases=%u fragment_colors=%u all_indices=256 rows=160\n",phases,phases*40960);return 0;
}
