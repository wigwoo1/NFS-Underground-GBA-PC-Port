#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "preview_resources.h"
#include "layer_snapshot.h"
#include "obj_tile.h"
#include "obj_affine_gpu.h"
#include "obj_effect_gpu.h"
#include "obj_candidate_effect_gpu.h"
static unsigned half(const uint8_t*p){return p[0]|((unsigned)p[1]<<8);}
static void quad(void){glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();}
int main(int argc,char**argv){
 if(argc!=4&&argc!=5)return 1;int zero_coverage=argc==5;NFHardwareLayerRow*row=malloc(sizeof(*row));FILE*f=fopen(argv[1],"rb");if(!row||!f)return 2;int ok=fread(row,1,sizeof(*row),f)==sizeof(*row);fclose(f);if(!ok)return 3;
 unsigned display=half(row->registers),blend=half(row->registers+0x50),alpha=half(row->registers+0x52),brightness=half(row->registers+0x54),priority=half(row->registers+0xc)&3;
 /* Unprepared candidate colors only support none/alpha effects here. */
 if(((blend>>6)&3)>=2)return 4;
 uint32_t colors[38400],tags[38400],metadata[38400];if(!nf_obj_layer(row->vram,sizeof(row->vram),row->palette,sizeof(row->palette),row->oam,sizeof(row->oam),display,colors,tags))return 5;
 for(unsigned i=0;i<38400;i++)metadata[i]=0xff000000u|(tags[i]&3)|(((tags[i]>>2)&3)<<8);
 int error=preview_context_open();if(error)return error;preview_generation++;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);
 const char*gradient="#version 120\nvoid main(){vec2 p=floor(gl_FragCoord.xy);gl_FragColor=vec4(mod(p.x,256.0),mod(p.y,256.0),mod(floor(p.x/16.0)+floor(p.y/16.0),256.0),255.0)/255.0;}";
 const char*coverage="#version 120\nvoid main(){vec2 p=floor(gl_FragCoord.xy);float a=mod(floor((p.x+0.25)/53.0)+floor((p.y+0.25)/47.0),2.0)*255.0;gl_FragColor=vec4(mod(p.x,256.0),mod(p.y,256.0),mod(floor(p.x/16.0)+floor(p.y/16.0),256.0),a)/255.0;}";
 if(!obj_shader_create(zero_coverage?coverage:gradient))return 6;obj_use(obj_affine_program);quad();obj_use(0);
 GLuint background;glGenTextures(1,&background);glBindTexture(GL_TEXTURE_2D,background);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,3840,2160,0);
 GLuint color=preview_texture(240,160,(uint8_t*)colors),meta=preview_texture(240,160,(uint8_t*)metadata);if(!color||!meta||!obj_shader_create(obj_candidate_effect_fragment))return 7;obj_use(obj_affine_program);
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");if(!active||!uniform1)return 8;
 active(0x84c0);glBindTexture(GL_TEXTURE_2D,color);uniform1(obj_location(obj_affine_program,"candidateColor"),0);active(0x84c1);glBindTexture(GL_TEXTURE_2D,meta);uniform1(obj_location(obj_affine_program,"candidateMetadata"),1);active(0x84c2);glBindTexture(GL_TEXTURE_2D,background);uniform1(obj_location(obj_affine_program,"nativeBackground"),2);
 unsigned bd=half(row->palette);uint32_t backdrop=0xff000000u|((bd&31)*255/31)|(((bd>>5&31)*255/31)<<8)|(((bd>>10&31)*255/31)<<16);
 obj_uniform4(obj_location(obj_affine_program,"backdropColor"),backdrop&255,backdrop>>8&255,backdrop>>16&255,1);
 obj_uniform4(obj_location(obj_affine_program,"effectParameters"),blend>>6&3,0,0,priority);
 obj_uniform4(obj_location(obj_affine_program,"firstTargets"),!!(blend&16),!!(blend&4),!!(blend&32),0);obj_uniform4(obj_location(obj_affine_program,"secondTargets"),!!(blend&4096),!!(blend&1024),!!(blend&8192),0);
 unsigned ea=alpha&31,eb=alpha>>8&31,ey=brightness&31;obj_uniform4(obj_location(obj_affine_program,"coefficients"),ea>16?16:ea,eb>16?16:eb,ey>16?16:ey,0);quad();obj_use(0);active(0x84c0);
 uint32_t*pixels=malloc(3840u*2160*4);if(!pixels)return 9;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);if(glGetError()!=GL_NO_ERROR)return 10;f=fopen(argv[2],"wb");if(!f)return 11;ok=fwrite(pixels,4,3840u*2160,f)==3840u*2160;fclose(f);if(!ok)return 12;
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<3840;x++){unsigned yy=2159-y;uint32_t bg=0xff000000u|(x&255)|((yy&255)<<8)|(((x/16+yy/16)&255)<<16),o=0,t=UINT32_MAX;if(zero_coverage&&!((x/53+yy/47)&1))bg=0;if(x>=300&&x<3540){unsigned sx=(unsigned)((x-300+.5)/13.5),sy=(unsigned)((y+.5)/13.5),i=sy*240+sx;o=colors[i];t=tags[i];}pixels[y*3840+x]=nf_obj_bg_backdrop_pixel(o,t,bg,priority,backdrop,blend,alpha,brightness);}
 f=fopen(argv[3],"wb");if(!f)return 13;ok=fwrite(pixels,4,3840u*2160,f)==3840u*2160;fclose(f);free(pixels);free(row);preview_shutdown();printf("candidate_metadata=1 target=3840x2160 cpu_overlap_resolution=1\n");return ok?0:14;
}


