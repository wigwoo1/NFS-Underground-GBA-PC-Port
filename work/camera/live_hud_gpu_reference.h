/* Opt-in scanline-owned HUD research pass; unsupported states fail. */
#include "obj_tile.h"
#include "obj_affine_gpu.h"
#include "obj_effect_gpu.h"
#include "obj_candidate_effect_gpu.h"
static unsigned hud_half(const uint8_t*p){return p[0]|((unsigned)p[1]<<8);}
static int endpoint_hud(void){
 if(!hud_preview)return 1;
 static GLuint background,program;static NFHudLayerRow row,previous;
 static uint8_t vram[0x18000];static uint32_t colors[38400],tags[38400],metadata[38400];
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");if(!active||!uniform1)return 0;
 if(!program){if(!obj_shader_create(obj_candidate_effect_fragment))return 0;program=obj_affine_program;}
 glPushAttrib(GL_ALL_ATTRIB_BITS);active(0x84c0);
 if(!background){glGenTextures(1,&background);glBindTexture(GL_TEXTURE_2D,background);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,3840,2160,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);}
 glBindTexture(GL_TEXTURE_2D,background);glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,0,0,0,3840,2160);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glDisable(GL_ALPHA_TEST);glEnable(GL_SCISSOR_TEST);obj_use(program);
 active(0x84c2);glBindTexture(GL_TEXTURE_2D,background);uniform1(obj_location(program,"nativeBackground"),2);uniform1(obj_location(program,"candidateColor"),0);uniform1(obj_location(program,"candidateMetadata"),1);
 int ok=1,have=0;GLuint color=0,meta=0;
 for(unsigned y=0;y<160;y++){
  if(!layer_read(hud_epoch,hud_refresh,y,&row,sizeof(row))||row.refresh!=hud_refresh||row.row!=y){ok=0;break;}
  unsigned display=hud_half(row.registers),blend=hud_half(row.registers+0x50),alpha=hud_half(row.registers+0x52),brightness=hud_half(row.registers+0x54),priority=hud_half(row.registers+0xc)&3;
  if((display&0xe080)||((display&7)!=4)||((blend>>6)&3)>=2){ok=0;break;}
  if(!have||display!=hud_half(previous.registers)||memcmp(row.obj_vram,previous.obj_vram,sizeof(row.obj_vram))||memcmp(row.palette,previous.palette,sizeof(row.palette))||memcmp(row.oam,previous.oam,sizeof(row.oam))){
   memcpy(vram+0x10000,row.obj_vram,sizeof(row.obj_vram));if(!nf_obj_layer(vram,sizeof(vram),row.palette,sizeof(row.palette),row.oam,sizeof(row.oam),display,colors,tags)){ok=0;break;}
   for(unsigned i=0;i<38400;i++)metadata[i]=0xff000000u|(tags[i]&3)|(((tags[i]>>2)&3)<<8);
   active(0x84c0);color=preview_texture(240,160,(uint8_t*)colors);meta=preview_texture(240,160,(uint8_t*)metadata);if(!color||!meta){ok=0;break;}previous=row;have=1;
  }
  active(0x84c0);glBindTexture(GL_TEXTURE_2D,color);active(0x84c1);glBindTexture(GL_TEXTURE_2D,meta);
  unsigned bd=hud_half(row.palette);obj_uniform4(obj_location(program,"backdropColor"),((bd&31)<<3)|((bd&31)>>2),((bd>>5&31)<<3)|((bd>>5&31)>>2),((bd>>10&31)<<3)|((bd>>10&31)>>2),1);
  obj_uniform4(obj_location(program,"effectParameters"),blend>>6&3,0,0,priority);obj_uniform4(obj_location(program,"firstTargets"),!!(blend&16),!!(blend&4),!!(blend&32),0);obj_uniform4(obj_location(program,"secondTargets"),!!(blend&4096),!!(blend&1024),!!(blend&8192),0);
  unsigned ea=alpha&31,eb=alpha>>8&31,ey=brightness&31;obj_uniform4(obj_location(program,"coefficients"),ea>16?16:ea,eb>16?16:eb,ey>16?16:ey,0);
  int top=(int)ceil(y*13.5-.5),bottom=(int)ceil((y+1)*13.5-.5);glScissor(0,2160-bottom,3840,bottom-top);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();
 }
 obj_use(0);active(0x84c0);glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glPopAttrib();if(ok)hud_drawn++;else hud_failed++;return ok;
}
