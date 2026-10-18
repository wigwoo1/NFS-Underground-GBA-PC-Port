
#ifndef NF_LIVE_SKY_ADAPTER_H
#define NF_LIVE_SKY_ADAPTER_H
#include "sky_phase.h"
/* Original initial-page fill/copy ownership only. Never sample rasterized 3D. */
static int live_sky_enabled,live_sky_dirty,live_sky_background_only;
static unsigned live_sky_refresh,live_sky_draw_calls,live_sky_snapshot_misses,live_sky_source_updates,live_sky_image_changes;
static uint64_t live_sky_image_hash;
static uint64_t live_sky_epoch,live_sky_capture_epoch;
static uint32_t live_sky_table[32768];
static uint8_t live_sky_vram[0x18000],live_sky_coverage[0x18000],live_sky_rgba[38400*4];
static GLuint live_sky_texture,live_sky_upper_texture,live_sky_program;
static int live_sky_continuous,live_sky_continuous_ready,live_sky_warming,live_sky_plane_dirty=1;
static uint8_t*live_sky_rom;static size_t live_sky_rom_bytes;
static uint8_t live_sky_lower_rgba[38400*4],live_sky_upper_rgba[38400*4];
static double live_sky_weight,live_sky_phase,live_sky_alpha,live_sky_target,live_sky_last_phase=-1;
static unsigned live_sky_continuous_frames,live_sky_phase_changes,live_sky_subpixel_frames,live_sky_continuous_fallbacks;
static unsigned live_sky_pair_older,live_sky_pair_newer;
static FILE*live_sky_phase_log;
static int live_sky_prepare_pair(const NFScenePacket*,const NFScenePacket*,const NFTimelineSample*);
static int live_sky_draw_background(void);
static int(*live_sky_plan_fn)(const char*,const void*,unsigned);
static int(*live_sky_vram_fn)(unsigned,void*,unsigned);
static int(*live_sky_coverage_fn)(unsigned,void*,unsigned);
static int(*live_sky_context_fn)(uint64_t,unsigned,uint32_t*);
/* Single-owner immutable sky inputs, keyed to the same scene serial/epoch
   as geometry. This queue does not yet change sky rendering or its cadence. */
static int live_sky_boundary_enabled;
static unsigned live_sky_boundaries_retained,live_sky_boundary_failures,live_sky_boundary_last_serial;
static uint64_t live_sky_boundary_epoch;
static struct {uint64_t epoch;unsigned serial,begin,end;uint8_t data[15192],asset[15376];int asset_usable;} live_sky_boundaries[16];
static int(*live_sky_boundary_read_fn)(uint64_t,uint32_t,unsigned,void*,size_t,size_t*);
static int live_sky_retain_boundary(uint64_t epoch,const NFScenePacket*packet){
 if(!live_sky_boundary_enabled)return 1;
 uint8_t data[15192];size_t written=0;uint32_t h[14];
 if(!live_sky_boundary_read_fn(epoch,packet->serial,0,data,sizeof(data),&written)||written!=sizeof(data)){live_sky_boundary_failures++;return 0;}
 NFSkyBoundary boundary;
 if(!nf_sky_boundary_decode(data,sizeof(data),&boundary)||boundary.epoch!=epoch||
    boundary.refresh<packet->begin_refresh||boundary.refresh>packet->end_refresh){live_sky_boundary_failures++;return 0;}
 if(live_sky_boundary_epoch!=epoch){memset(live_sky_boundaries,0,sizeof(live_sky_boundaries));live_sky_boundary_epoch=epoch;}
 unsigned slot=packet->serial%16;
 memcpy(live_sky_boundaries[slot].data,data,sizeof(data));
 live_sky_boundaries[slot].epoch=epoch;live_sky_boundaries[slot].serial=packet->serial;
 live_sky_boundaries[slot].begin=packet->begin_refresh;live_sky_boundaries[slot].end=packet->end_refresh;
 live_sky_boundaries[slot].asset_usable=0;
 if(live_sky_continuous&&boundary.origin>=0x08000000){
  size_t offset=boundary.origin-0x08000000;
  if(offset<=live_sky_rom_bytes&&live_sky_rom_bytes-offset>=NF_SKY_ASSET_BYTES&&
     nf_sky_asset_verify(&boundary,live_sky_rom+offset,NF_SKY_ASSET_BYTES)){
   memcpy(live_sky_boundaries[slot].asset,live_sky_rom+offset,NF_SKY_ASSET_BYTES);
   live_sky_boundaries[slot].asset_usable=1;
  }
 }
 live_sky_boundaries_retained++;live_sky_boundary_last_serial=packet->serial;return 1;
}
static int live_sky_program_create(void){
 if(live_sky_program)return 1;
 const char*fs="#version 120\nuniform sampler2D skyLower,skyUpper;uniform float skyWeight;void main(){vec2 p=floor(vec2(gl_FragCoord.x-300.0,2160.0-gl_FragCoord.y)/13.5);vec2 uv=(p+vec2(0.5))/vec2(240.0,160.0);vec4 c=mix(texture2D(skyLower,uv),texture2D(skyUpper,uv),skyWeight);if(c.a<0.5)discard;gl_FragColor=c;}";
 GLuint saved=obj_affine_program;int ok=obj_shader_create(fs);GLuint made=obj_affine_program;obj_affine_program=saved;
 if(!ok){if(made&&made!=saved){void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");if(remove)remove(made);}return 0;}
 live_sky_program=made;return 1;
}
static void live_sky_make_planes(const NFSkySample*sample){
 memcpy(live_sky_lower_rgba,live_sky_rgba,sizeof(live_sky_rgba));memcpy(live_sky_upper_rgba,live_sky_rgba,sizeof(live_sky_rgba));
 for(unsigned i=0;i<NF_SKY_COPY_BYTES;i++){
  unsigned at=10560+i,y=at/240;
  const uint8_t*palette=live_hud_rows[y].palette;
  unsigned indices[2]={sample->lower[i],sample->upper[i]};
  uint8_t*dest[2]={live_sky_lower_rgba+at*4,live_sky_upper_rgba+at*4};
  for(unsigned side=0;side<2;side++){
   unsigned color=palette[indices[side]*2]|((unsigned)palette[indices[side]*2+1]<<8);
   for(unsigned k=0;k<3;k++){unsigned v=(color>>(5*k))&31;dest[side][k]=(v<<3)|(v>>2);}dest[side][3]=255;
  }
 }
 live_sky_weight=sample->weight;live_sky_phase=sample->phase;live_sky_plane_dirty=1;
}
static int live_sky_prepare_pair(const NFScenePacket*a,const NFScenePacket*b,const NFTimelineSample*time){
 if(!live_sky_continuous)return 1;
 unsigned ia=a->serial%16,ib=b->serial%16;
 if(live_sky_boundaries[ia].epoch!=time->epoch||live_sky_boundaries[ib].epoch!=time->epoch||
    live_sky_boundaries[ia].serial!=a->serial||live_sky_boundaries[ib].serial!=b->serial||
    live_sky_boundaries[ia].begin!=a->begin_refresh||live_sky_boundaries[ia].end!=a->end_refresh||
    live_sky_boundaries[ib].begin!=b->begin_refresh||live_sky_boundaries[ib].end!=b->end_refresh)return 0;
 NFSkyBoundary old,new;NFSkySample sample;
 if(!nf_sky_boundary_decode(live_sky_boundaries[ia].data,15192,&old)||!nf_sky_boundary_decode(live_sky_boundaries[ib].data,15192,&new))return 0;
 int sampled=live_sky_boundaries[ia].asset_usable&&live_sky_boundaries[ib].asset_usable&&
  nf_sky_phase_sample(&old,&new,live_sky_boundaries[ia].asset,15376,time->alpha,1,&sample);
 if(!sampled){sample=(NFSkySample){old.indices,old.indices,old.source-old.origin,0,0,0,1};live_sky_continuous_fallbacks++;}
 live_sky_make_planes(&sample);live_sky_alpha=time->alpha;live_sky_target=time->target;
 live_sky_pair_older=a->serial;live_sky_pair_newer=b->serial;live_sky_continuous_ready=1;return 1;
}
static void live_sky_upload(GLuint*texture,const uint8_t*pixels,int dirty){
 if(!*texture){glGenTextures(1,texture);glBindTexture(GL_TEXTURE_2D,*texture);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,0x812f);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,0x812f);
  glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 }else{glBindTexture(GL_TEXTURE_2D,*texture);if(dirty)glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,pixels);}
}
static int live_sky_draw_background(void){
 if(!live_sky_enabled)return 1;if(!live_sky_refresh)return 0;
 int continuous=live_sky_continuous&&live_sky_continuous_ready;
 void(APIENTRY*active)(GLenum)=(void*)wglGetProcAddress("glActiveTexture");
 void(APIENTRY*uniform1)(GLint,GLint)=(void*)wglGetProcAddress("glUniform1i");
 void(APIENTRY*uniformf)(GLint,GLfloat)=(void*)wglGetProcAddress("glUniform1f");
 if(continuous&&(!active||!uniform1||!uniformf||!live_sky_program_create()))return 0;
 GLint prior_program=0,prior_active=0;glGetIntegerv(0x8b8d,&prior_program);if(active)glGetIntegerv(0x84e0,&prior_active);
 glPushAttrib(GL_ALL_ATTRIB_BITS);
 glViewport(300,0,3240,2160);glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,240,160,0,-1,1);
 glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glDisable(GL_DEPTH_TEST);glDisable(GL_SCISSOR_TEST);glDisable(GL_BLEND);
 glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);glColor4f(1,1,1,1);
 if(active)active(0x84c0);
 if(continuous){
  live_sky_upload(&live_sky_texture,live_sky_lower_rgba,live_sky_plane_dirty);
  active(0x84c1);live_sky_upload(&live_sky_upper_texture,live_sky_upper_rgba,live_sky_plane_dirty);
  obj_use(live_sky_program);uniform1(obj_location(live_sky_program,"skyLower"),0);uniform1(obj_location(live_sky_program,"skyUpper"),1);
  uniformf(obj_location(live_sky_program,"skyWeight"),(GLfloat)live_sky_weight);live_sky_plane_dirty=0;
 }else live_sky_upload(&live_sky_texture,live_sky_rgba,live_sky_dirty);
 live_sky_dirty=0;
 glBegin(GL_QUADS);glTexCoord2i(0,0);glVertex2i(0,0);glTexCoord2i(1,0);glVertex2i(240,0);glTexCoord2i(1,1);glVertex2i(240,160);glTexCoord2i(0,1);glVertex2i(0,160);glEnd();
 if(continuous)obj_use((GLuint)prior_program);
 glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glMatrixMode(GL_MODELVIEW);glPopAttrib();
 if(active)active((GLenum)prior_active);
 if(!live_sky_warming){
  live_sky_draw_calls++;
  if(continuous){live_sky_continuous_frames++;if(live_sky_phase!=live_sky_last_phase)live_sky_phase_changes++;live_sky_last_phase=live_sky_phase;
   if(live_sky_weight>0&&live_sky_weight<1)live_sky_subpixel_frames++;
   if(live_sky_phase_log){LARGE_INTEGER stamp,freq;QueryPerformanceCounter(&stamp);QueryPerformanceFrequency(&freq);
    fprintf(live_sky_phase_log,"%u,%.9f,%llu,%u,%u,%.9f,%.9f,%.9f,%.9f\n",live_sky_draw_calls,stamp.QuadPart/(double)freq.QuadPart,(unsigned long long)live_sky_boundary_epoch,live_sky_pair_older,live_sky_pair_newer,live_sky_target,live_sky_alpha,live_sky_phase,live_sky_weight);
   }
  }
 }
 return glGetError()==GL_NO_ERROR;
}
static int live_sky_warmup(void){
 if(!live_sky_continuous)return 1;
 live_sky_warming=1;live_sky_continuous_ready=1;live_sky_refresh=1;
 int ok=live_sky_draw_background();glFinish();live_sky_refresh=0;live_sky_continuous_ready=0;live_sky_warming=0;return ok;
}
static int live_sky_enable(HMODULE bridge,uint64_t epoch,const char*rom_path){
 if(!getenv("NF_LIVE_SKY"))return 1;
 live_sky_continuous=getenv("NF_LIVE_SKY_CONTINUOUS")!=NULL;
 if(live_sky_continuous){
  FILE*rom=fopen(rom_path,"rb");if(!rom)return 0;
  if(fseek(rom,0,SEEK_END)){fclose(rom);return 0;}long length=ftell(rom);rewind(rom);
  if(length<NF_SKY_ASSET_BYTES||length>32*1024*1024){fclose(rom);return 0;}
  live_sky_rom=malloc((size_t)length);if(!live_sky_rom){fclose(rom);return 0;}
  if(fread(live_sky_rom,1,length,rom)!=(size_t)length){fclose(rom);free(live_sky_rom);live_sky_rom=NULL;return 0;}
  fclose(rom);live_sky_rom_bytes=length;
  const char*trace=getenv("NF_LIVE_SKY_PHASE_LOG");
  if(trace){live_sky_phase_log=fopen(trace,"w");if(!live_sky_phase_log)return 0;fprintf(live_sky_phase_log,"draw,seconds,epoch,older,newer,target,alpha,phase,weight\n");}
  packet_background_pair=live_sky_prepare_pair;
 }

 const char* table_path=getenv("NF_LIVE_SOURCE_TABLE");if(!table_path)return 0;
 FILE* file=fopen(table_path,"rb");if(!file)return 0;
 size_t n=fread(live_sky_table,1,sizeof(live_sky_table),file);int extra=fgetc(file);fclose(file);
 if(n!=sizeof(live_sky_table)||extra!=EOF)return 0;
 int(*world_trace)(const char*)=(void*)GetProcAddress(bridge,"nf_world_trace");
 live_sky_plan_fn=(void*)GetProcAddress(bridge,"nf_native_model_plan_trace");
 live_sky_vram_fn=(void*)GetProcAddress(bridge,"nf_native_live_background_vram");
 live_sky_coverage_fn=(void*)GetProcAddress(bridge,"nf_native_live_background_coverage");
 live_sky_context_fn=(void*)GetProcAddress(bridge,"nf_layer_queue_context");
 if(!hud_preview||!world_trace||!live_sky_plan_fn||!live_sky_vram_fn||!live_sky_coverage_fn||!live_sky_context_fn)return 0;
 if(getenv("NF_LIVE_BACKGROUND_ONLY")){
  int(*background_only)(int)=(void*)GetProcAddress(bridge,"nf_native_background_capture_only");
  if(!background_only||!background_only(1))return 0;
  live_sky_background_only=1;
 }
 if(!live_sky_plan_fn("",live_sky_table,sizeof(live_sky_table))||!world_trace(""))return 0;
 if(getenv("NF_LIVE_SKY_BOUNDARIES")){
  int(*enable)(int)=(void*)GetProcAddress(bridge,"nf_live_sky_capture_enable");
  live_sky_boundary_read_fn=(void*)GetProcAddress(bridge,"nf_live_completed_sky_read");
  if(!enable||!live_sky_boundary_read_fn||!enable(1))return 0;
  live_sky_boundary_enabled=1;
 }
 live_sky_enabled=1;live_sky_capture_epoch=epoch;preview_after_background=live_sky_draw_background;return 1;
}
static int live_sky_before_frame(uint64_t epoch){
 if(!live_sky_enabled||live_sky_capture_epoch==epoch)return 1;
 live_sky_refresh=0;live_sky_epoch=0;
 if(!live_sky_plan_fn("",live_sky_table,sizeof(live_sky_table)))return 0;
 live_sky_capture_epoch=epoch;return 1;
}
static int live_sky_select(uint64_t epoch,unsigned target){
 if(!live_sky_enabled)return 1;
 static NFHudLayerRow row;
 for(unsigned age=0;age<=9&&age<target;age++){
  unsigned refresh=target-age;uint32_t context[3];
  if(!live_sky_context_fn(epoch,refresh,context)||context[0]!=5||context[1]!=4||context[2]!=1)continue;
  if(live_sky_epoch==epoch&&live_sky_refresh==refresh)return 1;
  if(!live_sky_vram_fn(refresh,live_sky_vram,sizeof(live_sky_vram))||!live_sky_coverage_fn(refresh,live_sky_coverage,sizeof(live_sky_coverage)))continue;
  memset(live_sky_rgba,0,sizeof(live_sky_rgba));
  for(unsigned y=0;y<160;y++){
   if(!live_hud_row_fn(epoch,refresh,y,&row,sizeof(row))||row.refresh!=refresh||row.row!=y)return 0;
   unsigned page=(row.registers[0]&16)?0xa000:0;
   for(unsigned x=0;x<240;x++){
    unsigned at=page+y*240+x,mask=live_sky_coverage[at];if(mask>1)return 0;if(!mask)continue;
    unsigned index=live_sky_vram[at],color=row.palette[index*2]|((unsigned)row.palette[index*2+1]<<8);
    uint8_t* p=live_sky_rgba+(y*240+x)*4;
    for(unsigned k=0;k<3;k++){unsigned v=(color>>(k*5))&31;p[k]=(v<<3)|(v>>2);}p[3]=255;
   }
  }
  uint64_t hash=14695981039346656037ull;
  for(size_t i=0;i<sizeof(live_sky_rgba);i++){hash^=live_sky_rgba[i];hash*=1099511628211ull;}
  if(!live_sky_source_updates||hash!=live_sky_image_hash)live_sky_image_changes++;
  live_sky_image_hash=hash;live_sky_source_updates++;
  live_sky_epoch=epoch;live_sky_refresh=refresh;live_sky_dirty=1;return 1;
 }
 live_sky_snapshot_misses++;return 0;
}
static void live_sky_close(void){
 if(live_sky_phase_log){fclose(live_sky_phase_log);live_sky_phase_log=NULL;}
 if(live_sky_program){void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteProgram");if(remove)remove(live_sky_program);live_sky_program=0;}
 if(live_sky_upper_texture)glDeleteTextures(1,&live_sky_upper_texture);live_sky_upper_texture=0;
 free(live_sky_rom);live_sky_rom=NULL;live_sky_rom_bytes=0;packet_background_pair=NULL;live_sky_continuous_ready=0;
 if(live_sky_texture)glDeleteTextures(1,&live_sky_texture);live_sky_texture=0;live_sky_enabled=0;preview_after_background=NULL;live_sky_boundary_enabled=0;live_sky_boundary_read_fn=NULL;live_sky_boundary_epoch=0;memset(live_sky_boundaries,0,sizeof(live_sky_boundaries));
}
#endif
