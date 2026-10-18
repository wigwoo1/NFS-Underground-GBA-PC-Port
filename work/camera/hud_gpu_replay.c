#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "preview_resources.h"
#include "layer_snapshot.h"
#include "model_zero_gpu.h"
static int draw_wall_writes(void){
 uint8_t rgba[12]={255,0,0,255,255,0,0,255,255,0,0,255},states[3]={0,1,2};
 preview_zero_valid=1;for(unsigned y=0;y<160;y++)preview_zero_colors[y]=(uint16_t)((y*137)&32767);
 GLuint texture=wall_zero_texture(3,1,rgba,states);if(!texture||!wall_zero_begin(texture,states))return 0;
 glBegin(GL_QUADS);glTexCoord2d(0,0);glVertex2i(0,0);glTexCoord2d(1,0);glVertex2i(3840,0);glTexCoord2d(1,1);glVertex2i(3840,2160);glTexCoord2d(0,1);glVertex2i(0,2160);glEnd();model_zero_end(states);return 1;
}
static int hud_preview=1;static uint64_t hud_epoch=1;static unsigned hud_refresh=500,hud_drawn,hud_failed;
static NFHudLayerRow owned[160];
static int replay_read(uint64_t epoch,unsigned refresh,unsigned y,void*out,unsigned size){if(epoch!=1||refresh!=hud_refresh||y>=160||size!=sizeof(NFHudLayerRow))return 0;memcpy(out,owned+y,size);return 1;}
static int(*layer_read)(uint64_t,unsigned,unsigned,void*,unsigned)=replay_read;
#ifdef NF_HUD_REFERENCE
#include "live_hud_gpu_reference.h"
#else
#include "live_hud_gpu.h"
#endif
int main(int argc,char**argv){if(argc!=3&&argc!=4&&argc!=5)return 1;int wall_writes=argc==5&&!strcmp(argv[4],"--wall-writes"),zero_coverage=argc==5&&!wall_writes;FILE*f=fopen(argv[1],"rb");if(!f)return 2;int ok=fread(owned,sizeof(owned),1,f)==1;fclose(f);if(!ok)return 3;
 hud_refresh=owned[0].refresh;int error=preview_context_open();if(error)return error;preview_generation++;
 glViewport(0,0,3840,2160);glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();
 const char*gradient="#version 120\nvoid main(){vec2 p=floor(gl_FragCoord.xy);gl_FragColor=vec4(mod(p.x,256.0),mod(p.y,256.0),mod(floor(p.x/16.0)+floor(p.y/16.0),256.0),255.0)/255.0;}";
 const char*coverage="#version 120\nvoid main(){vec2 p=floor(gl_FragCoord.xy);float a=mod(floor((p.x+0.25)/53.0)+floor((p.y+0.25)/47.0),2.0)*255.0;gl_FragColor=vec4(mod(p.x,256.0),mod(p.y,256.0),mod(floor(p.x/16.0)+floor(p.y/16.0),256.0),a)/255.0;}";
 if(!obj_shader_create(zero_coverage?coverage:gradient))return 4;obj_use(obj_affine_program);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();obj_use(0);
#ifndef NF_HUD_REFERENCE
 /* Warmup changes the disposable target, so re-render the known background. */
 GLuint gradient_program=obj_affine_program;if(!endpoint_hud_warmup())return 10;obj_use(gradient_program);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();obj_use(0);
#endif
 if(wall_writes&&!draw_wall_writes())return 13;
 if(!endpoint_hud())return 5;uint8_t*rgba=malloc(3840u*2160*4);if(!rgba)return 6;glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,rgba);if(glGetError()!=GL_NO_ERROR)return 7;f=fopen(argv[2],"wb");if(!f)return 8;ok=fwrite(rgba,4,3840u*2160,f)==3840u*2160;fclose(f);
 if(ok&&argc>=4){
  uint8_t vram[0x18000]={0};uint32_t colors[2][38400],tags[2][38400];uint8_t control_plane[38400];uint32_t*out=(uint32_t*)rgba;
  for(unsigned sy=0;sy<160;sy++){
   NFHudLayerRow*r=owned+sy;memcpy(vram+0x10000,r->obj_vram,sizeof(r->obj_vram));unsigned display=hud_half(r->registers),blend=hud_half(r->registers+80),alpha=hud_half(r->registers+82),brightness=hud_half(r->registers+84),priority=hud_half(r->registers+12)&3,bd=hud_half(r->palette);
   uint16_t window[6];for(unsigned i=0;i<6;i++)window[i]=hud_half(r->registers+64+i*2);
   if(!nf_rect_window_layer(display,window,control_plane))return 11;
   for(unsigned k=0;k<2;k++)if(!nf_obj_layer_prepared(vram,sizeof(vram),r->palette,sizeof(r->palette),r->oam,sizeof(r->oam),display&~0xe000u,k?blend:blend&0x3f00,brightness,colors[k],tags[k]))return 11;
   uint32_t unused[240],unused_tags[240];uint8_t row_control[240],backdrop_control[240];if(!nf_obj_window_scanline_prepared(vram,sizeof(vram),r->palette,sizeof(r->palette),r->oam,sizeof(r->oam),display,sy,window,blend,brightness,unused,unused_tags,row_control,backdrop_control))return 11;
   unsigned red=bd&31,green=bd>>5&31,blue=bd>>10&31;uint32_t backdrop=0xff000000u|((red<<3)|(red>>2))|(((green<<3)|(green>>2))<<8)|(((blue<<3)|(blue>>2))<<16);
   unsigned top=(unsigned)ceil(sy*13.5-.5),bottom=(unsigned)ceil((sy+1)*13.5-.5);
   for(unsigned y=top;y<bottom;y++)for(unsigned x=0;x<3840;x++){unsigned yy=2159-y;uint32_t bg=0xff000000u|(x&255)|((yy&255)<<8)|(((x/16+yy/16)&255)<<16),color=0,tag=0x20000;if(zero_coverage&&!((x/53+yy/47)&1))bg=0;if(wall_writes){if(x>=1280&&x<2560)bg=0;else if(x>=2560)bg=0xff0000ffu;}if(x>=300&&x<3540){unsigned sx=(unsigned)((x-300+.5)/13.5),i=sy*240+sx;unsigned control=control_plane[i],key=!!(control&32),effective=key?blend:blend&0x3f00;if((display&0x1000)&&(control&16)){color=colors[key][i];tag=tags[key][i]|0x20000;}if(!(display&0x400)||!(control&4))bg=0;out[y*3840+x]=nf_obj_bg_backdrop_pixel(color,tag,bg,priority,backdrop,effective,alpha,brightness);if(!color&&!bg&&((blend>>6)&3)>=2&&(blend&32)&&((control^backdrop_control[sx])&32))out[y*3840+x]=nf_obj_bg_backdrop_pixel(0,0x20000,0,priority,backdrop,(backdrop_control[sx]&32)?blend:blend&0x3f00,alpha,brightness);continue;}out[y*3840+x]=nf_obj_bg_backdrop_pixel(color,tag,bg,priority,backdrop,blend,alpha,brightness);}
  }
  f=fopen(argv[3],"wb");if(!f)return 12;ok=fwrite(rgba,4,3840u*2160,f)==3840u*2160;fclose(f);
 }
 free(rgba);preview_shutdown();return ok?0:9;}

