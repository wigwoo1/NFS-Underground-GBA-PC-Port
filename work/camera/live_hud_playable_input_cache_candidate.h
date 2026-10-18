static int hud_input_cache_equal=-1,hud_storage_matches_cache;
static uint64_t hud_input_cache_hits,hud_input_copy_bytes;
/* Bounded diagnostic records, retained after close; no emulation or pixel changes. */
#define HUD_CPU_RECORD_FIELDS 11
#define HUD_CPU_RECORD_CAPACITY 16384
static uint64_t hud_cpu_records[HUD_CPU_RECORD_CAPACITY][HUD_CPU_RECORD_FIELDS];
static unsigned hud_cpu_record_count,hud_cpu_record_dropped;
static void hud_cpu_snapshot(uint64_t out[3]){
 uint64_t cycles=0;FILETIME c,e,k,u;out[0]=sky_stage_now();
 out[1]=QueryThreadCycleTime(GetCurrentThread(),&cycles)?cycles:UINT64_MAX;
 if(GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u))out[2]=(((uint64_t)k.dwHighDateTime<<32)|k.dwLowDateTime)+(((uint64_t)u.dwHighDateTime<<32)|u.dwLowDateTime);else out[2]=UINT64_MAX;
}
static uint64_t hud_cpu_difference(uint64_t a,uint64_t b){return a==UINT64_MAX||b==UINT64_MAX||b<a?UINT64_MAX:b-a;}
/* One-entry cache; exact owned bytes decide reuse, never pointer identity. */
static NFHudLayerRow sky_hud_cached_rows[160];static uint8_t sky_hud_cached_text[76800];
static uint64_t sky_hud_cached_epoch;static int sky_hud_cached_valid,sky_hud_cached_has_text;
static uint64_t sky_hud_cache_hits,sky_hud_cache_misses;
/* Opt-in scanline-owned HUD research pass; unsupported states fail. */
#include "obj_tile.h"
#include "obj_affine_gpu.h"
#include "obj_effect_gpu.h"
#include "obj_candidate_effect_gpu.h"
static unsigned hud_half(const uint8_t*p){return p[0]|((unsigned)p[1]<<8);}
static double hud_prepare_ms;static unsigned hud_candidate_builds,hud_effect_batches;
static GLuint hud_background,hud_program;
/* Warm the actual composition program/resources with synthetic inputs before
   the game clock starts. No emulation advance or future scene sampling. */
static int endpoint_hud_warmup(void){
 if(!hud_preview)return 1;
 if(!obj_shader_create(obj_candidate_effect_fragment))return 0;hud_program=obj_affine_program;
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");if(!active||!uniform1)return 0;
 glPushAttrib(GL_ALL_ATTRIB_BITS);active(0x84c0);glGenTextures(1,&hud_background);glBindTexture(GL_TEXTURE_2D,hud_background);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,3840,2160,0);
 GLuint empty;uint32_t zero=0;glGenTextures(1,&empty);glBindTexture(GL_TEXTURE_2D,empty);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,&zero);
 obj_use(hud_program);uniform1(obj_location(hud_program,"candidateColor"),0);uniform1(obj_location(hud_program,"candidateMetadata"),1);uniform1(obj_location(hud_program,"nativeBackground"),2);active(0x84c1);glBindTexture(GL_TEXTURE_2D,empty);active(0x84c2);glBindTexture(GL_TEXTURE_2D,hud_background);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glViewport(0,0,3840,2160);glDisable(GL_SCISSOR_TEST);glDisable(GL_ALPHA_TEST);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);
 glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();glFinish();int ok=glGetError()==GL_NO_ERROR;obj_use(0);active(0x84c0);glDeleteTextures(1,&empty);glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glPopAttrib();return ok;
}
static int endpoint_hud(void){
 if(sky_stage_profile)sky_hud_ticks[0]=sky_stage_now();
 if(!hud_preview)return 1;
 GLuint background=hud_background,program=hud_program;const NFHudLayerRow*row;
 static uint8_t vram[0x18000];static uint32_t colors[38400],tags[38400],final_colors[38400],metadata[38400],text_colors[38400];
 uint64_t hud_cpu_begin[3],hud_cpu_lookup[3],hud_cpu_prepare_begin[3],hud_cpu_prepare_end[3];hud_cpu_snapshot(hud_cpu_begin);unsigned hud_cpu_builds_before=hud_candidate_builds;
 uint8_t text_indices[240],text_coverage[240];int has_text=owned_submission&&nf_submission_text_row(owned_submission,hud_epoch,hud_refresh,0,text_indices,text_coverage);
 int reuse=sky_hud_cached_valid&&sky_hud_cached_epoch==hud_epoch&&sky_hud_cached_has_text==has_text&&!getenv("NF_SKY_HUD_NO_CACHE")&&(hud_input_cache_equal>=0?hud_input_cache_equal:!memcmp(sky_hud_cached_rows,owned_hud,sizeof(owned_hud)))&&(!has_text||(owned_text&&!memcmp(sky_hud_cached_text,owned_text,76800)));
 hud_cpu_snapshot(hud_cpu_lookup);
 if(reuse)sky_hud_cache_hits++;else{sky_hud_cache_misses++;memset(text_colors,0,sizeof(text_colors));}
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");if(!active||!uniform1)return 0;
 if(!program){if(!obj_shader_create(obj_candidate_effect_fragment))return 0;program=hud_program=obj_affine_program;}
 glPushAttrib(GL_ALL_ATTRIB_BITS);active(0x84c0);
 if(!background){glGenTextures(1,&background);hud_background=background;glBindTexture(GL_TEXTURE_2D,background);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,3840,2160,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);}
 glBindTexture(GL_TEXTURE_2D,background);glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,0,0,0,3840,2160);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glDisable(GL_ALPHA_TEST);glEnable(GL_SCISSOR_TEST);obj_use(program);
 active(0x84c2);glBindTexture(GL_TEXTURE_2D,background);uniform1(obj_location(program,"nativeBackground"),2);uniform1(obj_location(program,"candidateColor"),0);uniform1(obj_location(program,"candidateMetadata"),1);
 uniform1(obj_location(program,"ownedText"),3);uniform1(obj_location(program,"ownedTextEnabled"),has_text);
 int ok=1;GLuint color=0,meta=0,text=0;LARGE_INTEGER cpu_start,cpu_end,cpu_frequency;QueryPerformanceFrequency(&cpu_frequency);QueryPerformanceCounter(&cpu_start);
 if(sky_stage_profile)sky_hud_ticks[1]=sky_stage_now();
 hud_cpu_snapshot(hud_cpu_prepare_begin);
 if(!reuse)for(unsigned y=0;y<160;y++){
  row=owned_hud+y;
  if(row->refresh!=hud_refresh||row->row!=y){ok=0;break;}
  unsigned display=hud_half(row->registers),blend=hud_half(row->registers+0x50),alpha=hud_half(row->registers+0x52),brightness=hud_half(row->registers+0x54),priority=hud_half(row->registers+0xc)&3;
  if((display&0x8080)||((display&7)!=4)){ok=0;break;}
  if(has_text){
   if(!nf_submission_text_row(owned_submission,hud_epoch,hud_refresh,y,text_indices,text_coverage)){ok=0;break;}
   for(unsigned x=0;x<240;x++)if(text_coverage[x]){
    unsigned c=hud_half(row->palette+2*text_indices[x]);
    unsigned r=((c&31)<<3)|((c&31)>>2),g=((c>>5&31)<<3)|((c>>5&31)>>2),b=((c>>10&31)<<3)|((c>>10&31)>>2);
    text_colors[y*240+x]=0xff000000u|(b<<16)|(g<<8)|r;
   }
  }
  memcpy(vram+0x10000,row->obj_vram,sizeof(row->obj_vram));
  uint16_t window[6];uint8_t controls[240],backdrop_controls[240];for(unsigned i=0;i<6;i++)window[i]=(uint16_t)hud_half(row->registers+64+i*2);
  if(!nf_obj_window_scanline_prepared(vram,sizeof(vram),row->palette,sizeof(row->palette),row->oam,sizeof(row->oam),display,y,window,blend,brightness,colors,tags,controls,backdrop_controls)){ok=0;break;}
  hud_candidate_builds++;
  memcpy(final_colors+y*240,colors,240*4);
  for(unsigned x=0;x<240;x++){unsigned control=controls[x];if(!(display&0x400))control&=~4u;unsigned flags=128|control|((backdrop_controls[x]&32)?64:0);metadata[y*240+x]=0xff000000u|(flags<<16)|(tags[x]&3)|(((tags[x]>>2)&3)<<8);}
 }
 if(!reuse){sky_hud_cached_valid=ok;if(ok){memcpy(sky_hud_cached_rows,owned_hud,sizeof(owned_hud));if(has_text)memcpy(sky_hud_cached_text,owned_text,76800);sky_hud_cached_epoch=hud_epoch;sky_hud_cached_has_text=has_text;hud_storage_matches_cache=1;}}
 hud_cpu_snapshot(hud_cpu_prepare_end);
 if(hud_cpu_record_count<HUD_CPU_RECORD_CAPACITY){uint64_t *r=hud_cpu_records[hud_cpu_record_count++];r[0]=hud_epoch;r[1]=hud_refresh;r[2]=reuse;r[3]=has_text;r[4]=hud_cpu_difference(hud_cpu_begin[0],hud_cpu_lookup[0]);r[5]=hud_cpu_difference(hud_cpu_begin[1],hud_cpu_lookup[1]);r[6]=hud_cpu_difference(hud_cpu_prepare_begin[0],hud_cpu_prepare_end[0]);r[7]=hud_cpu_difference(hud_cpu_prepare_begin[1],hud_cpu_prepare_end[1]);r[8]=hud_cpu_difference(hud_cpu_prepare_begin[2],hud_cpu_prepare_end[2]);r[9]=hud_candidate_builds-hud_cpu_builds_before;r[10]=ok;}else hud_cpu_record_dropped++;
 QueryPerformanceCounter(&cpu_end);hud_prepare_ms+=(cpu_end.QuadPart-cpu_start.QuadPart)*1000.0/cpu_frequency.QuadPart;
 if(sky_stage_profile)sky_hud_ticks[2]=sky_stage_now();
 if(ok){active(0x84c0);color=preview_texture(240,160,(uint8_t*)final_colors);meta=preview_texture(240,160,(uint8_t*)metadata);if(!color||!meta)ok=0;if(has_text){text=preview_texture(240,160,(uint8_t*)text_colors);if(!text)ok=0;active(0x84c3);glBindTexture(GL_TEXTURE_2D,text);}}
 for(unsigned y=0;ok&&y<160;){
  row=owned_hud+y;hud_effect_batches++;unsigned blend=hud_half(row->registers+0x50),alpha=hud_half(row->registers+0x52),brightness=hud_half(row->registers+0x54),priority=hud_half(row->registers+0xc)&3;
  unsigned end=y+1;
  /* Batch only equal effect inputs; candidates already retain each exact row-> */
  while(end<160&&hud_half(owned_hud[end].palette)==hud_half(row->palette)&&
        (hud_half(owned_hud[end].registers+0xc)&3)==priority&&
        !memcmp(owned_hud[end].registers+0x50,row->registers+0x50,6))end++;
  active(0x84c0);glBindTexture(GL_TEXTURE_2D,color);active(0x84c1);glBindTexture(GL_TEXTURE_2D,meta);
  unsigned bd=hud_half(row->palette);obj_uniform4(obj_location(program,"backdropColor"),((bd&31)<<3)|((bd&31)>>2),((bd>>5&31)<<3)|((bd>>5&31)>>2),((bd>>10&31)<<3)|((bd>>10&31)>>2),1);
  obj_uniform4(obj_location(program,"effectParameters"),blend>>6&3,0,0,priority);obj_uniform4(obj_location(program,"firstTargets"),!!(blend&16),!!(blend&4),!!(blend&32),0);obj_uniform4(obj_location(program,"secondTargets"),!!(blend&4096),!!(blend&1024),!!(blend&8192),0);
  unsigned ea=alpha&31,eb=alpha>>8&31,ey=brightness&31;obj_uniform4(obj_location(program,"coefficients"),ea>16?16:ea,eb>16?16:eb,ey>16?16:ey,0);
  int top=(int)ceil(y*13.5-.5),bottom=(int)ceil(end*13.5-.5);glScissor(0,2160-bottom,3840,bottom-top);glBegin(GL_QUADS);glVertex2i(0,0);glVertex2i(3840,0);glVertex2i(3840,2160);glVertex2i(0,2160);glEnd();y=end;
 }
 obj_use(0);active(0x84c0);glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glPopAttrib();if(ok)hud_drawn++;else hud_failed++;if(sky_stage_profile)sky_hud_ticks[3]=sky_stage_now();return ok;
}
