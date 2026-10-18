/* Research-only snapshots at world transform, projection and road draw entries.
   Included after the bridge memory readers. No writes to emulated memory. */
static FILE* world_file;
static unsigned world_native_capture;
static FILE*owned_clip_store_file;static unsigned owned_clip_store_count;
API int nf_owned_clip_store_trace(const char*path){if(owned_clip_store_file)fclose(owned_clip_store_file);owned_clip_store_file=path?fopen(path,"wb"):NULL;owned_clip_store_count=0;return owned_clip_store_file!=NULL;}

static unsigned world_event_limit=20000;
API void nf_world_trace_limit(unsigned limit){world_event_limit=limit;}

#ifdef NF_VISIBILITY_CAPTURE
#include "native_scene_executor.h"
extern void nf_geometry_sources_reset(void);
extern int nf_geometry_sources_append(unsigned,unsigned,const uint8_t*const*,const unsigned*,unsigned);
extern int nf_geometry_sources_model(unsigned,const uint8_t*const*,const unsigned*,unsigned);
extern int nf_geometry_sources_close(unsigned);
static void*native_live_scene;static FILE*native_live_scene_file;
static struct {unsigned valid,refresh;uint64_t generation;uint8_t vram[0x18000];} native_live_frames[16];
static unsigned native_background_started,native_completed_scene_count;
API unsigned nf_native_live_scene_count(void){return native_completed_scene_count;}
static uint8_t native_background_building[0x18000],native_background_coverage[0x18000];
static struct {unsigned valid,refresh;uint8_t vram[0x18000],coverage[0x18000];} native_background_frames[16];
API unsigned nf_native_live_latest_frame(void){unsigned latest=0;for(unsigned i=0;i<16;i++)if(native_background_frames[i].valid&&native_background_frames[i].refresh>latest)latest=native_background_frames[i].refresh;return latest;}
API int nf_native_live_background_vram(unsigned refresh,void*out,unsigned bytes){unsigned slot=refresh%16;if(!out||bytes!=0x18000||!native_background_frames[slot].valid||native_background_frames[slot].refresh!=refresh)return 0;memcpy(out,native_background_frames[slot].vram,bytes);return 1;}
API int nf_native_live_background_coverage(unsigned refresh,void*out,unsigned bytes){unsigned slot=refresh%16;if(!out||bytes!=0x18000||!native_background_frames[slot].valid||native_background_frames[slot].refresh!=refresh)return 0;memcpy(out,native_background_frames[slot].coverage,bytes);return 1;}
API int nf_native_live_frame_vram(unsigned refresh,void*out,unsigned bytes,uint64_t*generation){
 unsigned slot=refresh%16;
 if(!out||!generation||bytes!=0x18000||!native_live_frames[slot].valid||native_live_frames[slot].refresh!=refresh)return 0;
 memcpy(out,native_live_frames[slot].vram,bytes);*generation=native_live_frames[slot].generation;return 1;
}
/* Worker-thread synchronous deep copy; caller owns the complete immutable frame.
   Reject stale epoch/refresh before publication; output is atomic on failure. */
API int nf_native_owned_frame_read(uint64_t epoch,unsigned refresh,void*out,size_t capacity,size_t*written){
 if(!written||!epoch||epoch!=nf_native_scene_epoch())return 0;
 unsigned slot=refresh%16;if(!native_background_frames[slot].valid||native_background_frames[slot].refresh!=refresh)return 0;
 size_t gn=0;extern int nf_geometry_sources_read(unsigned,void*,size_t,size_t*);if(!nf_geometry_sources_read(refresh,NULL,0,&gn)||!gn||gn>0x800000)return 0;
 size_t hn=160*sizeof(NFHudLayerRow),total=40+gn+hn+153600;if(out&&capacity<total)return 0;
 /* Size query publishes metadata only; full content validation occurs on read. */
 if(!out){*written=total;return 1;}
 uint8_t*packet=malloc(total);if(!packet)return 0;int ok=0;size_t actual=0;
 uint32_t header[6]={0x3346474e,refresh,(uint32_t)gn,(uint32_t)hn,76800,76800};uint64_t ticks=(uint64_t)refresh*280896;
 memcpy(packet,header,24);memcpy(packet+24,&epoch,8);memcpy(packet+32,&ticks,8);
 if(!nf_geometry_sources_read(refresh,packet+40,gn,&actual)||actual!=gn)goto done;
 uint8_t*background=packet+40+gn+hn,*text=background+76800;
 for(unsigned y=0;y<160;y++){
  NFHudLayerRow*row=(NFHudLayerRow*)(packet+40+gn+y*sizeof(NFHudLayerRow));
  if(!nf_layer_queue_hud_row(epoch,refresh,y,row,sizeof(*row))||row->refresh!=refresh||row->row!=y)goto done;
  unsigned page=(row->registers[0]&16)?0xa000:0,base=page+y*240;
  for(unsigned x=0;x<240;x++){unsigned mask=native_background_frames[slot].coverage[base+x];background[y*240+x]=mask?native_background_frames[slot].vram[base+x]:0;background[38400+y*240+x]=(uint8_t)mask;}
  if(!nf_layer_queue_text_row(epoch,refresh,y,text+y*240,text+38400+y*240,240))goto done;
 }
 if(epoch!=nf_native_scene_epoch())goto done;
 if(out)memcpy(out,packet,total);*written=total;ok=1;
 done:free(packet);return ok;
}
static void owned_graph_live_close(uint64_t,unsigned);
static void native_live_frame_close(void){
 owned_graph_live_close(nf_native_scene_epoch(),c->frameCounter(c)+1);
 if(!native_live_scene)return;
 unsigned refresh=c->frameCounter(c)+1,slot=refresh%16;nf_geometry_sources_close(refresh);uint64_t generation;
 if(native_background_started){native_completed_scene_count++;memcpy(native_background_frames[slot].vram,native_background_building,0x18000);memcpy(native_background_frames[slot].coverage,native_background_coverage,0x18000);native_background_frames[slot].valid=1;native_background_frames[slot].refresh=refresh;}native_background_started=0;memset(native_background_coverage,0,sizeof(native_background_coverage));
 if(nf_scene_snapshot(native_live_scene,native_live_frames[slot].vram,0x18000,&generation)){
  native_live_frames[slot].valid=1;native_live_frames[slot].refresh=refresh;native_live_frames[slot].generation=generation;
 }
}
extern int nfs_model_source_rows(const uint8_t*const[10],const unsigned[10],const uint32_t*,uint32_t*,unsigned,unsigned*);
extern int nfs_model_rows_write(const uint32_t*,unsigned,unsigned,uint32_t,const uint8_t*,size_t,uint8_t*,size_t);
extern int nfs_wall_source_columns(const uint8_t*,const uint32_t*,const unsigned*,const uint8_t*,const uint8_t*,const uint8_t*,uint32_t*,unsigned,unsigned*);
extern void *nf_road_scratch_create(void);
extern void nf_road_scratch_destroy(void*);
extern int nf_road_source_runs(void*,const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,const uint8_t*,unsigned,unsigned,const int32_t*,const uint16_t*,uint32_t,unsigned,const uint32_t*,uint32_t,unsigned,const uint32_t*,uint32_t*,unsigned,unsigned*,uint64_t*);
static unsigned native_plan_enabled;
static FILE*native_road_plan_file;static void*native_road_scratch;
static FILE*native_wall_plan_file;
static FILE*native_model_plan_file,*native_model_vram_file;static uint32_t native_model_plan_table[32768];
API int nf_native_model_plan_trace(const char*path,const void*table,unsigned bytes){
 native_plan_enabled=0;
 if(native_live_scene){nf_scene_destroy(native_live_scene);native_live_scene=NULL;}
 if(native_live_scene_file){fclose(native_live_scene_file);native_live_scene_file=NULL;}
 if(native_road_plan_file){fclose(native_road_plan_file);native_road_plan_file=NULL;}
 if(native_road_scratch){nf_road_scratch_destroy(native_road_scratch);native_road_scratch=NULL;}
 if(native_wall_plan_file){fclose(native_wall_plan_file);native_wall_plan_file=NULL;}
 if(native_model_vram_file){fclose(native_model_vram_file);native_model_vram_file=NULL;}
 if(native_model_plan_file){fclose(native_model_plan_file);native_model_plan_file=NULL;}
 nf_geometry_sources_reset();native_completed_scene_count=0;memset(native_background_coverage,0,sizeof(native_background_coverage));
 memset(native_live_frames,0,sizeof(native_live_frames));memset(native_background_frames,0,sizeof(native_background_frames));native_background_started=0;
 if(!path)return 1;
 if(!table||bytes!=sizeof(native_model_plan_table))return 0;
 memcpy(native_model_plan_table,table,bytes);
 /* Empty path enables owned native execution without diagnostic files. */
 if(!*path){native_road_scratch=nf_road_scratch_create();native_plan_enabled=native_road_scratch!=NULL;return native_plan_enabled;}
 native_plan_enabled=1;native_model_plan_file=fopen(path,"wb");char imagepath[1400];snprintf(imagepath,sizeof(imagepath),"%s.vram.bin",path);native_model_vram_file=fopen(imagepath,"wb");snprintf(imagepath,sizeof(imagepath),"%s.wall.bin",path);native_wall_plan_file=fopen(imagepath,"wb");snprintf(imagepath,sizeof(imagepath),"%s.road.bin",path);native_road_plan_file=fopen(imagepath,"wb");native_road_scratch=nf_road_scratch_create();snprintf(imagepath,sizeof(imagepath),"%s.scene.bin",path);native_live_scene_file=fopen(imagepath,"wb");return native_model_plan_file!=NULL&&native_model_vram_file!=NULL&&native_wall_plan_file!=NULL&&native_road_plan_file!=NULL&&native_road_scratch!=NULL;
}
static int native_read_owned(unsigned address,void*out,unsigned bytes){
 if(!validmem(address,bytes))return 0;
 for(unsigned j=0;j<bytes;j++)((uint8_t*)out)[j]=c->busRead8(c,address+j);return 1;
}
static int native_live_submit(unsigned kind,const uint32_t*commands,unsigned count,unsigned shift,unsigned address,unsigned texture_bytes,int start){
 if(!native_live_scene&&start)native_live_scene=nf_scene_create((const uint8_t*)((struct GBA*)c->board)->video.renderer->vram,0x18000);
 if(!native_live_scene)return 1;
 if(kind>=1&&kind<=3&&!native_background_started){uint64_t generation;if(!nf_scene_snapshot(native_live_scene,native_background_building,0x18000,&generation))return 0;native_background_started=1;}
 uint8_t*texture=texture_bytes?malloc(texture_bytes):NULL;int ok=!texture_bytes||(texture&&native_read_owned(address,texture,texture_bytes));
 NFSceneEvent event={kind,count,shift,address,commands,texture,texture_bytes,NULL,NULL};
 if(ok)ok=nf_scene_submit(native_live_scene,&event,1);
 if(ok&&!native_background_started&&kind>=4&&kind<=6){unsigned offset=commands[0];
  if(kind==4){unsigned n=(commands[2]>>5)*32;memset(native_background_coverage+offset,1,n);}
  else if(kind==6){unsigned n=(commands[1]>>5)*32;memset(native_background_coverage+offset,1,n);}
  else{unsigned n=((commands[1]>>5)+1)*32,rows=commands[2],stride=commands[4]&~3u;for(unsigned y=0;y<rows;y++)memset(native_background_coverage+offset+y*stride,1,n);}
 }
 if(native_live_scene_file){uint32_t header[5]={0x3153534e,c->frameCounter(c),kind,(unsigned)ok,count};fwrite(header,sizeof(header),1,native_live_scene_file);}
 free(texture);return ok;
}
static void native_live_compare(unsigned kind){
 if(!native_live_scene||!native_live_scene_file)return;
 uint8_t*vram=malloc(0x18000);uint64_t generation;unsigned differences=0;int ok=vram&&nf_scene_snapshot(native_live_scene,vram,0x18000,&generation);
 if(ok){const uint8_t*actual=(const uint8_t*)((struct GBA*)c->board)->video.renderer->vram;for(unsigned i=0;i<0x18000;i++)differences+=vram[i]!=actual[i];}
 uint32_t header[5]={0x3143534e,c->frameCounter(c),kind,(unsigned)ok,ok?differences:0xffffffff};fwrite(header,sizeof(header),1,native_live_scene_file);free(vram);
}
static void native_road_plan_capture(unsigned material,unsigned state,unsigned descriptor,unsigned source,unsigned count,unsigned uv,unsigned stack){
 if(!native_plan_enabled||!native_road_scratch)return;
 uint8_t vertices[32*68],offsets[32*32],face[20]={0},mat[48],matrix[48];uint16_t bounds[4];uint32_t uv_offsets[2];unsigned runs=0;uint64_t missing=0;
 uint32_t*out=malloc(8192*17*sizeof(*out));int ok=out&&native_read_owned(source,vertices,count*68)&&native_read_owned(material,mat,48)&&native_read_owned(rd32(state+0x54),matrix,48);
 for(unsigned i=0;i<count&&ok;i++){
  unsigned index=rd16(source+i*68+42);memset(offsets+i*32,0,32);
  if(index!=65535)ok=native_read_owned(rd32(state+24)+index*32,offsets+i*32,32);
 }
 unsigned face_index=rd16(descriptor+10);if(ok&&face_index!=65535)ok=native_read_owned(rd32(state+28)+face_index*20,face,20);
 for(unsigned i=0;i<4;i++)bounds[i]=rd16(state+226+i*2);
 uv_offsets[0]=(uint32_t)(int32_t)(int16_t)rd16(uv+4);uv_offsets[1]=(uint32_t)(int32_t)(int16_t)rd16(uv+6);
 if(ok)ok=nf_road_source_runs(native_road_scratch,vertices,count*68,offsets,count*32,face,mat,count,rd32(stack),(const int32_t*)matrix,bounds,rd32(state+0x6c),rd16(state+242),native_model_plan_table,rd32(rd32(state+0x50)),rd32(stack+4),uv_offsets,out,8192,&runs,&missing);
 uint32_t header[7]={0x3152504e,c->frameCounter(c),state,(unsigned)ok,ok?runs:0,(uint32_t)missing,(uint32_t)(missing>>32)};if(native_road_plan_file)fwrite(header,sizeof(header),1,native_road_plan_file);
 if(ok&&native_road_plan_file)fwrite(out,17*sizeof(*out),runs,native_road_plan_file);
 if(ok&&!missing){unsigned shift=(uint16_t)mat[36]|((unsigned)mat[37]<<8),height=(uint16_t)mat[38]|((unsigned)mat[39]<<8);native_live_submit(1,out,runs,shift,rd32(material+40),(1u<<shift)*height*2,1);}
 if(ok&&!missing){
  unsigned texture_bytes=(1u<<(unsigned)(uint16_t)(mat[36]|((unsigned)mat[37]<<8)))*(unsigned)(uint16_t)(mat[38]|((unsigned)mat[39]<<8))*2;
  uint8_t*texture=malloc(texture_bytes),palette[512],desc[48],animation[64],frame[64];uint32_t config[8]={count,rd32(stack),rd32(stack+4),rd16(state+242),rd32(state+0x6c),rd32(rd32(state+0x50)),uv_offsets[0],uv_offsets[1]};
  if(texture&&native_read_owned(rd32(material+40),texture,texture_bytes)&&native_read_owned(descriptor,desc,48)&&native_read_owned(uv,animation,64)&&native_read_owned(rd32(state+0x50),frame,64)){
   for(unsigned j=0;j<512;j++)palette[j]=c->busRead8(c,0x05000000+j);
   const uint8_t*blocks[12]={vertices,offsets,face,mat,matrix,(const uint8_t*)bounds,(const uint8_t*)config,texture,palette,desc,animation,frame};unsigned sizes[12]={count*68,count*32,20,48,48,8,32,texture_bytes,512,48,64,64};nf_geometry_sources_append(1,state,blocks,sizes,12);
  }free(texture);
 }
 free(out);
}
extern int nf_wall_owned_prepared(const uint8_t*,const uint8_t*,const uint8_t*,const int32_t*,const uint8_t*,unsigned,const uint32_t*,uint8_t*);
static struct {unsigned state,source,count,descriptor;} native_wall_owners[32];
static void native_wall_plan_capture(unsigned material,unsigned state,unsigned descriptor,unsigned source,unsigned flags){
 if(!native_plan_enabled)return;
 unsigned addresses[4]={rd32(material+12),material,rd32(state+0x50),descriptor};
 unsigned sizes[4]={52,48,64,32};uint8_t owned[4][64]={{0}};unsigned bounds[4],count=0;uint32_t columns[2400];int ok=1;
 for(unsigned i=1;i<4&&ok;i++){
  if(!validmem(addresses[i],sizes[i])){ok=0;break;}
  for(unsigned j=0;j<sizes[i];j++)owned[i][j]=c->busRead8(c,addresses[i]+j);
 }
 if(validmem(addresses[0],sizes[0]))native_read_owned(addresses[0],owned[0],sizes[0]); /* Optional diagnostic comparison only. */
 for(unsigned i=0;i<4;i++)bounds[i]=rd16(state+226+i*2);
 if(ok){
  uint8_t vertex[136],offset[64]={0},animation[8]={0},matrix[48],context[260],palette[512],*texture=malloc(0x10000);unsigned index=rd16(source+42),mi=rd16(source+44),base_material=rd32(state+32)+mi*32;
  int captured=texture&&native_read_owned(source,vertex,68)&&native_read_owned(rd32(state+0x54),matrix,48)&&native_read_owned(state,context,256)&&native_read_owned(rd32(material+40),texture,0x10000);
  if(captured&&index!=65535)captured=native_read_owned(rd32(state+24)+index*32,offset,32);
  unsigned next_source=0;
  for(unsigned j=0;j<32;j++)if(native_wall_owners[j].state==state){unsigned base=native_wall_owners[j].source,n=native_wall_owners[j].count;
   if(n&&source>=base&&(source-base)%68==0&&(source-base)/68<n)next_source=base+(((source-base)/68+1)%n)*68;break;}
  if(captured)captured=next_source&&native_read_owned(next_source,vertex+68,68);
  if(captured){unsigned next_index=rd16(next_source+42);if(next_index!=65535)captured=native_read_owned(rd32(state+24)+next_index*32,offset+32,32);memcpy(context+256,&flags,4);}
  if(captured)captured=validmem(base_material,32)&&native_read_owned(rd32(state+72)+rd16(base_material)*8,animation,8);
  uint8_t prepared[52];
  if(captured)captured=nf_wall_owned_prepared(vertex,offset,animation,(const int32_t*)matrix,owned[1],flags,native_model_plan_table,prepared);
  if(captured)captured=nfs_wall_source_columns(prepared,native_model_plan_table,bounds,owned[1],owned[2],owned[3],columns,120,&count);
  uint32_t header[5]={0x3157504e,c->frameCounter(c),state,(unsigned)captured,captured?count:0};if(native_wall_plan_file)fwrite(header,sizeof(header),1,native_wall_plan_file);
  if(captured){if(native_wall_plan_file)fwrite(columns,20*sizeof(*columns),count,native_wall_plan_file);native_live_submit(2,columns,count,0,rd32(material+40),0x10000,0);}
  if(captured){for(unsigned j=0;j<512;j++)palette[j]=c->busRead8(c,0x05000000+j);
   uint16_t clip[4];for(unsigned i=0;i<4;i++)clip[i]=(uint16_t)bounds[i];
   const uint8_t*blocks[12]={vertex,offset,animation,matrix,owned[1],(const uint8_t*)clip,owned[2],owned[3],texture,palette,owned[0],context};unsigned sizes[12]={136,64,8,48,48,8,64,32,0x10000,512,52,260};nf_geometry_sources_append(2,state,blocks,sizes,12);
  }free(texture);
 }
}
static void native_model_plan_capture(unsigned context,const unsigned addresses[10],const unsigned sizes[10]){
 if(!native_plan_enabled)return;
 uint8_t*owned[10]={0};uint32_t*rows=malloc(65536*7*sizeof(*rows));unsigned count=0;int ok=rows!=NULL;
 for(unsigned i=0;i<10&&ok;i++){
  if(!sizes[i]||!validmem(addresses[i],sizes[i])){ok=0;break;}
  owned[i]=malloc(sizes[i]);if(!owned[i]){ok=0;break;}
  for(unsigned j=0;j<sizes[i];j++)owned[i][j]=c->busRead8(c,addresses[i]+j);
 }
 if(ok)ok=nfs_model_source_rows((const uint8_t*const*)owned,sizes,native_model_plan_table,rows,65536,&count);
 uint32_t header[5]={0x314d504e,c->frameCounter(c),context,(unsigned)ok,ok?count:0};if(native_model_plan_file)fwrite(header,sizeof(header),1,native_model_plan_file);
 if(ok&&native_model_plan_file)fwrite(rows,7*sizeof(*rows),count,native_model_plan_file);
 if(ok){unsigned shift=owned[0][56]|((unsigned)owned[0][57]<<8),height=owned[0][58]|((unsigned)owned[0][59]<<8);uint32_t address;memcpy(&address,owned[0]+52,4);native_live_submit(3,rows,count,shift,address,(1u<<shift)*height,0);}
 if(ok){
  unsigned shift=owned[0][56]|((unsigned)owned[0][57]<<8),height=owned[0][58]|((unsigned)owned[0][59]<<8);uint32_t texture_address;memcpy(&texture_address,owned[0]+52,4);
  size_t texture_size=shift<=10&&height<=1024?((size_t)1<<shift)*height:0;uint8_t*texture=texture_size?malloc(texture_size):NULL,*vram=malloc(0x18000);int written=texture&&vram&&validmem(texture_address,(unsigned)texture_size);
  if(written){for(unsigned j=0;j<texture_size;j++)texture[j]=c->busRead8(c,texture_address+j);memcpy(vram,((struct GBA*)c->board)->video.renderer->vram,0x18000);written=nfs_model_rows_write(rows,count,shift,texture_address,texture,texture_size,vram,0x18000);}
  if(written){const uint8_t*blocks[12];unsigned bytes[12];for(unsigned i=0;i<10;i++){blocks[i]=owned[i];bytes[i]=sizes[i];}uint8_t palette[512];for(unsigned j=0;j<512;j++)palette[j]=c->busRead8(c,0x05000000+j);blocks[10]=texture;bytes[10]=(unsigned)texture_size;blocks[11]=palette;bytes[11]=512;nf_geometry_sources_model(context,blocks,bytes,12);}
  uint32_t image_header[4]={0x31564d4e,c->frameCounter(c),context,(unsigned)written};if(native_model_vram_file){fwrite(image_header,sizeof(image_header),1,native_model_vram_file);if(written)fwrite(vram,0x18000,1,native_model_vram_file);}free(texture);free(vram);
 }

 for(unsigned i=0;i<10;i++)free(owned[i]);free(rows);
}
#endif

static unsigned world_events;
static unsigned sprite_writes_enabled,sprite_write_count,sprite_write_overflow;
static unsigned initial_writes_enabled,initial_surface_seen,initial_write_count,initial_write_overflow;
static uint32_t initial_writes[512][7];
static unsigned world_framebuffer_enabled,world_framebuffer_draws;
static struct {uint32_t id,pc,lr,sp,state,source,writes,write_bytes,polygon_calls;} world_framebuffer_pending[8];
static unsigned world_framebuffer_pending_count;
static void world_framebuffer_write(unsigned address,unsigned size){
 if(owned_clip_store_file&&owned_clip_store_count<8192&&c->frameCounter(c)>=8754&&c->frameCounter(c)<=8780&&address<0x0200875c&&address+size>0x020086bc){
  struct ARMCore*cpu=c->cpu;uint32_t record[21]={0x3153434e,cpu->gprs[15]-(cpu->cpsr.t?4:8),c->frameCounter(c),address,size};memcpy(record+5,cpu->gprs,64);fwrite(record,sizeof(record),1,owned_clip_store_file);owned_clip_store_count++;
 }

 if(world_file&&sprite_writes_enabled&&address>=0x06014000&&address<0x06018000){
  if(sprite_write_count<4096&&world_events<world_event_limit){
   sprite_write_count++;struct ARMCore*sprite_cpu=c->cpu;
   uint32_t header[21]={0x3157464e,0xffff0101,c->frameCounter(c),world_events++,1};
   memcpy(header+5,sprite_cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
   uint32_t metadata[3]={sprite_cpu->gprs[15]-(sprite_cpu->cpsr.t?4:8),address,size},block[3]={101,0,sizeof(metadata)};
   fwrite(block,sizeof(block),1,world_file);fwrite(metadata,sizeof(metadata),1,world_file);
  }else sprite_write_overflow++;
 }

 if(world_file&&initial_writes_enabled&&!initial_surface_seen&&(address>>24)==6){
  struct ARMCore*cpu=c->cpu;unsigned pc=cpu->gprs[15]-(cpu->cpsr.t?4:8),i=0;
  for(;i<initial_write_count;i++)if(initial_writes[i][0]==pc)break;
  if(i==initial_write_count){
   if(i>=512){initial_write_overflow++;goto initial_done;}
   initial_write_count++;memset(initial_writes[i],0,sizeof(initial_writes[i]));initial_writes[i][0]=pc;initial_writes[i][1]=cpu->gprs[14];initial_writes[i][4]=address;initial_writes[i][6]=c->frameCounter(c);
  }
  initial_writes[i][2]++;initial_writes[i][3]+=size;
  if(address<initial_writes[i][4])initial_writes[i][4]=address;
  if(address+size>initial_writes[i][5])initial_writes[i][5]=address+size;
 }
initial_done:

 if(!world_file||!world_framebuffer_enabled||!world_framebuffer_pending_count||(address>>24)!=6)return;
 unsigned i=world_framebuffer_pending_count-1;world_framebuffer_pending[i].writes++;world_framebuffer_pending[i].write_bytes+=size;
}
/* Optional bounded original draw-entry/return snapshots. Direct owned file
   copy from VRAM; no bus writes, cycle changes or rendering substitutions. */
static void world_framebuffer_record(struct ARMCore*cpu,unsigned stage,unsigned index){
 if(stage==1)native_live_compare(world_framebuffer_pending[index].pc);
 uint32_t header[21]={0x3157464e,0xffff0084,c->frameCounter(c),world_events++,2};
 memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
 uint32_t metadata[11]={stage,world_framebuffer_pending[index].id,world_framebuffer_pending[index].pc,world_framebuffer_pending[index].lr,world_framebuffer_pending[index].sp,world_framebuffer_pending[index].state,world_framebuffer_pending[index].source,rd16(0x04000000),world_framebuffer_pending[index].writes,world_framebuffer_pending[index].write_bytes,world_framebuffer_pending[index].polygon_calls};
 uint32_t block[3]={85,0,sizeof(metadata)};fwrite(block,sizeof(block),1,world_file);fwrite(metadata,sizeof(metadata),1,world_file);
 uint32_t image[3]={84,0x06000000,0x18000};fwrite(image,sizeof(image),1,world_file);
 fwrite(((struct GBA*)c->board)->video.renderer->vram,0x18000,1,world_file);
}
static void world_framebuffer_trace(struct ARMCore*cpu,unsigned pc){
 if(!world_framebuffer_enabled)return;
 if(pc==0x03003d24&&world_framebuffer_pending_count)world_framebuffer_pending[world_framebuffer_pending_count-1].polygon_calls++;
 if(world_framebuffer_pending_count){unsigned i=world_framebuffer_pending_count-1;
  /* 04770 is after a BL: LR points back to 04770, not to this draw's
     caller. Its source epilogue starts at048B0 with the saved entry SP. */
  int model_exit=world_framebuffer_pending[i].pc==0x03004770&&pc==0x030048b0&&!cpu->cpsr.t;
  int other_return=world_framebuffer_pending[i].pc!=0x03004770&&pc==(world_framebuffer_pending[i].lr&~1u)&&cpu->cpsr.t==(world_framebuffer_pending[i].lr&1u);
  if((model_exit||other_return)&&cpu->gprs[13]==world_framebuffer_pending[i].sp){
   world_framebuffer_record(cpu,1,i);world_framebuffer_pending_count--;
  }
 }
 if((pc!=0x030032f0&&pc!=0x03000304&&pc!=0x03004770)||world_framebuffer_draws>=128||world_framebuffer_pending_count>=8)return;
 unsigned i=world_framebuffer_pending_count++;
 memset(world_framebuffer_pending+i,0,sizeof(world_framebuffer_pending[i]));
 world_framebuffer_pending[i].id=world_framebuffer_draws++;world_framebuffer_pending[i].pc=pc;world_framebuffer_pending[i].lr=cpu->gprs[14];world_framebuffer_pending[i].sp=cpu->gprs[13];
 world_framebuffer_pending[i].state=pc==0x03004770?cpu->gprs[4]:cpu->gprs[1];world_framebuffer_pending[i].source=pc==0x030032f0?cpu->gprs[7]:pc==0x03000304?cpu->gprs[6]:cpu->gprs[4];
 world_framebuffer_record(cpu,0,i);
}
/* A display-page flip closes the geometry batch prepared on the back page.
   Header register slots 0/1 carry old/new DISPCNT; no memory blocks follow. */
static void world_flip(unsigned old_value,unsigned new_value){
 native_live_frame_close();
 /* A routine may return after the page flip that closes its draw scene.
    Preserve its exact closing framebuffer without inventing an early return. */
 if(world_file&&world_framebuffer_enabled&&world_events<world_event_limit)
  for(unsigned i=0;i<world_framebuffer_pending_count;i++)world_framebuffer_record(c->cpu,2,i);
 initial_surface_seen=0;initial_write_count=initial_write_overflow=0;
 native_scene_flip(new_value);
 if(!world_file||world_events>=world_event_limit)return;
 const char* display_option=getenv("NF_TRACE_DISPLAY_SNAPSHOTS");
 unsigned display_snapshot=display_option&&!strcmp(display_option,"1");
 const char* sprite_option=getenv("NF_TRACE_SPRITE_SNAPSHOTS");
 unsigned sprite_snapshot=display_snapshot&&sprite_option&&!strcmp(sprite_option,"1");
 uint32_t header[21]={0x3157464e,0x04000000,c->frameCounter(c),world_events++,display_snapshot?(sprite_snapshot?6:2):0};
 header[5]=old_value;header[6]=new_value;fwrite(header,sizeof(header),1,world_file);
 if(display_snapshot){
  unsigned page=(new_value&16)?0xa000:0;
  uint32_t image[3]={92,0x06000000+page,240*160};
  fwrite(image,sizeof(image),1,world_file);
  fwrite((uint8_t*)((struct GBA*)c->board)->video.renderer->vram+page,240*160,1,world_file);
  uint32_t palette[3]={67,0x05000000,512};fwrite(palette,sizeof(palette),1,world_file);
  for(unsigned i=0;i<512;i++)fputc(c->busRead8(c,0x05000000+i),world_file);
  if(sprite_snapshot){
   /* Shadow IO retains write-only window/blend registers; bus reads do not. */
   uint32_t video_io[3]={103,0x04000000,0x60};fwrite(video_io,sizeof(video_io),1,world_file);
   uint16_t registers[0x30];memcpy(registers,((struct GBA*)c->board)->memory.io,sizeof(registers));
   registers[0]=(uint16_t)new_value;fwrite(registers,sizeof(registers),1,world_file);

   uint32_t obj[3]={98,0x06014000,0x4000};fwrite(obj,sizeof(obj),1,world_file);
   fwrite((uint8_t*)((struct GBA*)c->board)->video.renderer->vram+0x14000,0x4000,1,world_file);
   uint32_t oam[3]={99,0x07000000,1024};fwrite(oam,sizeof(oam),1,world_file);
   for(unsigned i=0;i<1024;i++)fputc(c->busRead8(c,0x07000000+i),world_file);
   uint32_t palette_obj[3]={100,0x05000200,512};fwrite(palette_obj,sizeof(palette_obj),1,world_file);
   for(unsigned i=0;i<512;i++)fputc(c->busRead8(c,0x05000200+i),world_file);
  }
 }
}
static void world_block(unsigned tag,unsigned address,unsigned size){
 uint32_t header[3]={tag,address,(validmem(address,size)||(tag==67&&address==0x05000000&&size==512))?size:0};
 fwrite(header,sizeof(header),1,world_file);
 for(unsigned i=0;i<header[2];i++)fputc(c->busRead8(c,address+i),world_file);
}
/* Native source collection survives diagnostic budget exhaustion. Same bounded
   raw-source validation as diagnostic dispatch; never imports screen polygons. */
static void world_native_after_limit(struct ARMCore*cpu,unsigned pc){
 if(native_live_scene&&(pc==0x030002c0||pc==0x03003814||pc==0x03000298)&&cpu->gprs[0]>=0x06000000&&cpu->gprs[0]<0x06018000){
  uint32_t commands[5]={cpu->gprs[0]-0x06000000,cpu->gprs[2],cpu->gprs[3],0,0};
  if(pc==0x030002c0){commands[1]=cpu->gprs[1];commands[2]=cpu->gprs[2];native_live_submit(4,commands,1,0,0,0,0);}
  else if(pc==0x03000298)native_live_submit(6,commands,1,0,cpu->gprs[1],(cpu->gprs[2]>>5)*32,0);
  else {commands[3]=rd32(cpu->gprs[13]);commands[4]=rd32(cpu->gprs[13]+4);unsigned rows=commands[2],bytes=rows?((rows-1)*(commands[3]&~1u)+((commands[1]>>5)+1)*32):0;native_live_submit(5,commands,1,0,cpu->gprs[1],bytes,0);}
 }

 if(pc==0x03004770){
  unsigned context=cpu->gprs[pc==0x030045e0?0:4];
  if(!validmem(context,68))return;
  unsigned descriptor=rd32(context+12);
  if(!validmem(descriptor,40))return;
  unsigned count=rd16(descriptor+36),source=rd32(context+16)+rd32(descriptor)*6;
  if(count>2048)return;
  unsigned faces=rd16(descriptor+34),face_sizes=rd32(context+44)+rd32(descriptor+28);
  unsigned indices=0;
  if(faces>512||!validmem(face_sizes,faces))return;
  for(unsigned i=0;i<faces;i++){unsigned n=c->busRead8(c,face_sizes+i);if(n<3||n>32)return;indices+=n;}
  if(indices>4096)return;
  unsigned vertex_indices=rd32(context+32)+rd32(descriptor+4)*2;
  unsigned uv_indices=rd32(context+36)+rd32(descriptor+24)*2,max_uv=0;
  if(!validmem(vertex_indices,indices*2)||!validmem(uv_indices,indices*2))return;
  for(unsigned i=0;i<indices;i++){unsigned index=rd16(uv_indices+i*2);if(index>max_uv)max_uv=index;}
  if(max_uv>4095)return;
  unsigned uv=rd32(context+20);
  if(rd16(descriptor+32)&1)uv+=rd32(descriptor+8)*4;
  unsigned shift=rd16(context+56),height=rd16(context+58);
  unsigned texture_size=shift<=10&&height<=1024?(1u<<shift)*height:0;
  unsigned frame_context=rd32(context+8);
#ifdef NF_VISIBILITY_CAPTURE
  unsigned addresses[10]={context,descriptor,rd32(context+60),frame_context,source,face_sizes,vertex_indices,uv_indices,uv,rd32(frame_context+4)};
  unsigned sizes[10]={68,40,48,64,count*6,faces,indices*2,indices*2,(max_uv+1)*4,16};native_model_plan_capture(context,addresses,sizes);
#endif
  return;
 }
 if(pc==0x03000304){
  unsigned material=cpu->gprs[0],state=cpu->gprs[1],source=cpu->gprs[6];
  if(validmem(material,48)&&validmem(state,256)&&validmem(source,68))native_wall_plan_capture(material,state,cpu->gprs[3],source,cpu->gprs[2]);
  return;
 }
 if(pc!=0x03000d48&&pc!=0x03001800&&pc!=0x03002964&&pc!=0x030032f0)return;
 unsigned state=pc==0x030032f0?cpu->gprs[1]:pc==0x03002964?cpu->gprs[5]:cpu->gprs[0];
 if(!validmem(state,256))return;
 unsigned descriptor=pc==0x03000d48?cpu->gprs[1]:pc==0x03001800?cpu->gprs[3]:cpu->gprs[7];
 if(!validmem(descriptor,48))return;
 unsigned count=rd16(descriptor+2);
 if(!count||count>32)return;
 unsigned source=rd32(state+16)+rd16(descriptor)*68;
 if(pc==0x03001800){unsigned slot=32;for(unsigned j=0;j<32;j++)if(native_wall_owners[j].state==state){slot=j;break;}
  if(slot==32)for(unsigned j=0;j<32;j++)if(!native_wall_owners[j].state){slot=j;break;}
  if(slot==32)slot=(state>>2)%32;native_wall_owners[slot].state=state;native_wall_owners[slot].source=source;native_wall_owners[slot].count=count;native_wall_owners[slot].descriptor=descriptor;}
 if(pc==0x030032f0)native_road_plan_capture(cpu->gprs[0],state,descriptor,source,count,cpu->gprs[2],cpu->gprs[13]);
}
static unsigned owned_graph_live_enabled,owned_graph_live_material_failed;
static uint8_t*owned_graph_live_callback_data;static size_t owned_graph_live_callback_bytes;static unsigned owned_graph_live_callback_failed;
API int nf_owned_graph_live_callbacks_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_callback_failed)return 0;*bytes=owned_graph_live_callback_bytes;if(!out)return 1;if(capacity<*bytes)return 0;if(*bytes)memcpy(out,owned_graph_live_callback_data,*bytes);return 1;}
static unsigned owned_eligibility_region_id;
static FILE*owned_input_list_file;static unsigned owned_input_list_count;
API int nf_owned_input_list_trace(const char*path){if(owned_input_list_file)fclose(owned_input_list_file);owned_input_list_file=path?fopen(path,"wb"):NULL;owned_input_list_count=0;return owned_input_list_file!=NULL;}
static void owned_input_list_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_input_list_file||owned_input_list_count>=512||pc!=0x03002000||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[0],head=cpu->gprs[1],index=head,count=0,ok=1;if(!validmem(state,256))return;
 unsigned base=rd32(state+60),camera=rd32(state+84);if(!validmem(camera,48))return;uint8_t entries[512*168];unsigned seen[512];
 while(index!=65535){if(count==512||index>65534){ok=0;break;}unsigned duplicate=0;for(unsigned j=0;j<count;j++)if(seen[j]==index)duplicate=1;if(duplicate){ok=0;break;}
 unsigned address=base+index*164;if(address<base||!validmem(address,164)){ok=0;break;}seen[count]=index;memcpy(entries+count*168,&index,4);native_read_owned(address,entries+count*168+4,164);index=rd16(address+2);count++;}
 uint32_t h[8]={0x31494f4e,c->frameCounter(c),state,head,owned_eligibility_region_id,count,count*168,ok};uint8_t matrix[48];native_read_owned(camera,matrix,48);fwrite(h,sizeof(h),1,owned_input_list_file);fwrite(matrix,sizeof(matrix),1,owned_input_list_file);fwrite(entries,168,count,owned_input_list_file);owned_input_list_count++;
}
static FILE*owned_eligibility_file;static unsigned owned_eligibility_count;
API int nf_owned_eligibility_trace(const char*path){if(owned_eligibility_file)fclose(owned_eligibility_file);owned_eligibility_file=path?fopen(path,"wb"):NULL;owned_eligibility_count=0;return owned_eligibility_file!=NULL;}
static void owned_eligibility_trace(struct ARMCore*cpu,unsigned pc){
 if((!owned_eligibility_file&&!owned_graph_live_enabled)||(pc!=0x03002044&&pc!=0x03002090)||(!owned_graph_live_enabled&&(owned_eligibility_count>=2048||c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 unsigned state=cpu->gprs[7],object=cpu->gprs[6],camera=rd32(state+84);if(!validmem(object,164)||!validmem(camera,48))return;
 unsigned visited=pc==0x03002044?((cpu->gprs[12]>>cpu->gprs[0])&1):0;
 uint32_t h[8]={0x31454f4e,c->frameCounter(c),pc,state,object,visited,owned_eligibility_count++,owned_eligibility_region_id};uint8_t data[212];native_read_owned(object,data,164);native_read_owned(camera,data+164,48);if(owned_eligibility_file){fwrite(h,sizeof(h),1,owned_eligibility_file);fwrite(data,sizeof(data),1,owned_eligibility_file);}
 if(owned_graph_live_enabled){size_t at=owned_graph_live_callback_bytes;if(at>0x100000-244)owned_graph_live_callback_failed=1;else if(!owned_graph_live_callback_failed){uint8_t*next=realloc(owned_graph_live_callback_data,at+244);if(!next)owned_graph_live_callback_failed=1;else{memcpy(next+at,h,32);memcpy(next+at+32,data,212);owned_graph_live_callback_data=next;owned_graph_live_callback_bytes+=244;}}}
}
static FILE*owned_filter_file;static unsigned owned_filter_count;
API int nf_owned_filter_trace(const char*path){if(owned_filter_file)fclose(owned_filter_file);owned_filter_file=path?fopen(path,"wb"):NULL;owned_filter_count=0;return owned_filter_file!=NULL;}
static void owned_filter_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_filter_file||owned_filter_count>=2048||pc!=0x030020f0||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[7],object=cpu->gprs[6],camera=rd32(state+84);if(!validmem(object,164)||!validmem(camera,48))return;
 uint32_t h[8]={0x31464f4e,c->frameCounter(c),state,object,cpu->gprs[0],cpu->gprs[4],cpu->gprs[2],owned_filter_count++};uint8_t data[212];native_read_owned(object,data,164);native_read_owned(camera,data+164,48);fwrite(h,sizeof(h),1,owned_filter_file);fwrite(data,sizeof(data),1,owned_filter_file);
}
static uint8_t*owned_graph_live_association_data;static size_t owned_graph_live_association_bytes;static unsigned owned_graph_live_association_failed;
API int nf_owned_graph_live_associations_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_association_failed)return 0;*bytes=owned_graph_live_association_bytes;if(!out)return 1;if(capacity<*bytes)return 0;if(*bytes)memcpy(out,owned_graph_live_association_data,*bytes);return 1;}
static FILE*owned_association_file;static unsigned owned_association_count;
API int nf_owned_association_trace(const char*path){if(owned_association_file)fclose(owned_association_file);owned_association_file=path?fopen(path,"wb"):NULL;owned_association_count=0;return owned_association_file!=NULL;}
static void owned_association_trace(struct ARMCore*cpu,unsigned pc){
 if((!owned_association_file&&!owned_graph_live_enabled)||pc!=0x030054a0||(!owned_graph_live_enabled&&(owned_association_count>=512||c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 owned_eligibility_region_id=owned_association_count;
 unsigned state=cpu->gprs[0],parent=cpu->gprs[1];if(!validmem(state,256)||!validmem(parent,16))return;unsigned index=rd16(parent),descriptor=rd32(state+20)+index*48,entry=rd32(state+12)+index*2;if(!validmem(descriptor,48)||!validmem(entry,2))return;
 uint32_t h[8]={0x3241534e,c->frameCounter(c),state,index,rd16(entry),descriptor,entry,owned_association_count++};uint8_t data[368];native_read_owned(parent,data,16);native_read_owned(descriptor,data+16,48);native_read_owned(state,data+64,256);native_read_owned(rd32(state+84),data+320,48);if(owned_association_file){fwrite(h,sizeof(h),1,owned_association_file);fwrite(data,sizeof(data),1,owned_association_file);}
 if(owned_graph_live_enabled){size_t at=owned_graph_live_association_bytes;if(at>0x100000-400)owned_graph_live_association_failed=1;else if(!owned_graph_live_association_failed){uint8_t*next=realloc(owned_graph_live_association_data,at+400);if(!next)owned_graph_live_association_failed=1;else{memcpy(next+at,h,32);memcpy(next+at+32,data,368);owned_graph_live_association_data=next;owned_graph_live_association_bytes+=400;}}}
}
static FILE*owned_chain_file;static unsigned owned_chain_count;
API int nf_owned_chain_trace(const char*path){if(owned_chain_file)fclose(owned_chain_file);owned_chain_file=path?fopen(path,"wb"):NULL;owned_chain_count=0;return owned_chain_file!=NULL;}
static void owned_chain_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_chain_file||owned_chain_count>=512||pc!=0x0300220c||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[0],parent=cpu->gprs[1],head=rd32(0x030070e0),index=head,count=0,ok=1;
 if(!validmem(state,256)||!validmem(parent,16))return;
 unsigned base=rd32(state+60);uint8_t entries[512*168];unsigned seen[512];
 while(index!=65535){if(count==512||index>65534){ok=0;break;}unsigned duplicate=0;for(unsigned j=0;j<count;j++)if(seen[j]==index)duplicate=1;if(duplicate){ok=0;break;}
 unsigned address=base+index*164;if(address<base||!validmem(address,164)){ok=0;break;}seen[count]=index;memcpy(entries+count*168,&index,4);native_read_owned(address,entries+count*168+4,164);index=rd16(address+4);count++;}
 uint32_t h[8]={0x3148434e,c->frameCounter(c),state,head,parent,count,count*168,ok};uint8_t sources[272];native_read_owned(parent,sources,16);native_read_owned(state,sources+16,256);fwrite(h,sizeof(h),1,owned_chain_file);fwrite(sources,sizeof(sources),1,owned_chain_file);fwrite(entries,168,count,owned_chain_file);owned_chain_count++;
}
static uint8_t*owned_graph_live_supplement_texture_data;static size_t owned_graph_live_supplement_texture_bytes;static unsigned owned_graph_live_supplement_texture_failed;
API int nf_owned_graph_live_supplement_textures_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_supplement_texture_failed)return 0;*bytes=owned_graph_live_supplement_texture_bytes;if(!out)return 1;if(capacity<*bytes)return 0;if(*bytes)memcpy(out,owned_graph_live_supplement_texture_data,*bytes);return 1;}
static FILE*owned_supplement_textures_file;static unsigned owned_supplement_textures_count;
API int nf_owned_supplement_textures_trace(const char*path){if(owned_supplement_textures_file)fclose(owned_supplement_textures_file);owned_supplement_textures_file=path?fopen(path,"wb"):NULL;owned_supplement_textures_count=0;return owned_supplement_textures_file!=NULL;}
static void owned_supplement_textures_trace(struct ARMCore*cpu,unsigned pc){
 if((!owned_supplement_textures_file&&!owned_graph_live_enabled)||pc!=0x030027f0||cpu->gprs[14]!=0x03002364||(!owned_graph_live_enabled&&(owned_supplement_textures_count>=2048||c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 unsigned state=cpu->gprs[0],parent=cpu->gprs[1];if(!validmem(state,256)||!validmem(parent,16))return;unsigned id=rd16(parent),desc=rd32(state+20)+id*48;if(!validmem(desc,48))return;unsigned n=rd16(desc+2),points=rd32(state+16)+rd16(desc)*68;if(!n||n>32||!validmem(points,n*68))return;
 for(unsigned j=0;j<n;j++){unsigned mi=rd16(points+j*68+44),phase=0,shift=0,height=0,address=0,size=0,ok=0;uint8_t sources[72]={0};uint8_t*texture=NULL;
 if(mi!=65535){unsigned base=rd32(state+32)+mi*32;if(validmem(base,32)){unsigned animation=rd32(state+72)+rd16(base)*8;if(validmem(animation,8)){phase=rd16(animation+2);unsigned resolved=base+phase*32;if(validmem(resolved,32)){shift=rd16(resolved+26);height=rd16(resolved+10);address=rd32(state)+rd32(resolved+4);if(shift<=10&&height<=1024){size=(1u<<shift)*height;if(size&&size<=0x10000&&validmem(address,size)){texture=malloc(size);ok=texture&&native_read_owned(base,sources,32)&&native_read_owned(animation,sources+32,8)&&native_read_owned(resolved,sources+40,32)&&native_read_owned(address,texture,size);}}}}}}
 uint32_t h[12]={0x3154534e,c->frameCounter(c),state,id,j,mi,phase,shift,height,address,ok?size:0,ok};if(owned_supplement_textures_file){fwrite(h,sizeof(h),1,owned_supplement_textures_file);fwrite(sources,1,72,owned_supplement_textures_file);if(ok)fwrite(texture,1,size,owned_supplement_textures_file);}
 if(owned_graph_live_enabled){size_t bytes=120+(ok?size:0),at=owned_graph_live_supplement_texture_bytes;if(!ok||bytes>0x800000-at)owned_graph_live_supplement_texture_failed=1;else if(!owned_graph_live_supplement_texture_failed){uint8_t*next=realloc(owned_graph_live_supplement_texture_data,at+bytes);if(!next)owned_graph_live_supplement_texture_failed=1;else{memcpy(next+at,h,48);memcpy(next+at+48,sources,72);memcpy(next+at+120,texture,size);owned_graph_live_supplement_texture_data=next;owned_graph_live_supplement_texture_bytes+=bytes;}}}free(texture);owned_supplement_textures_count++;}
}
static uint8_t*owned_graph_live_supplement_data;static size_t owned_graph_live_supplement_bytes;static unsigned owned_graph_live_supplement_failed;
API int nf_owned_graph_live_supplements_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_supplement_failed)return 0;*bytes=owned_graph_live_supplement_bytes;if(!out)return 1;if(capacity<*bytes)return 0;if(*bytes)memcpy(out,owned_graph_live_supplement_data,*bytes);return 1;}
static FILE*owned_supplement_geometry_file;static unsigned owned_supplement_geometry_count;
API int nf_owned_supplement_geometry_trace(const char*path){if(owned_supplement_geometry_file)fclose(owned_supplement_geometry_file);owned_supplement_geometry_file=path?fopen(path,"wb"):NULL;owned_supplement_geometry_count=0;return owned_supplement_geometry_file!=NULL;}
static void owned_supplement_geometry_trace(struct ARMCore*cpu,unsigned pc){
 if((!owned_supplement_geometry_file&&!owned_graph_live_enabled)||pc!=0x030027f0||cpu->gprs[14]!=0x03002364||(!owned_graph_live_enabled&&(owned_supplement_geometry_count>=512||c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 unsigned state=cpu->gprs[0],parent=cpu->gprs[1];if(!validmem(state,256)||!validmem(parent,16))return;unsigned id=rd16(parent),desc=rd32(state+20)+id*48;if(!validmem(desc,48))return;unsigned n=rd16(desc+2),points=rd32(state+16)+rd16(desc)*68;if(!n||n>32||!validmem(points,n*68))return;
 uint8_t data[944+32*140]={0};int ok=native_read_owned(desc,data,48)&&native_read_owned(rd32(state+84),data+48,48)&&native_read_owned(rd32(state+80),data+96,64)&&native_read_owned(parent,data+160,16)&&native_read_owned(state,data+176,256);
 for(unsigned j=0;j<512;j++)data[432+j]=c->busRead8(c,0x05000000+j);
 for(unsigned j=0;j<n&&ok;j++){unsigned source=points+j*68,offset=rd16(source+42),mi=rd16(source+44),material=rd32(state+32)+mi*32;uint8_t*v=data+944+j*140;
 ok=native_read_owned(source,v,68);if(ok&&offset!=65535)ok=native_read_owned(rd32(state+24)+offset*32,v+68,32);if(ok&&mi!=65535)ok=native_read_owned(material,v+100,32)&&native_read_owned(rd32(state+72)+rd16(material)*8,v+132,8);}
 uint32_t h[8]={0x3147534e,c->frameCounter(c),state,id,n,944+n*140,(unsigned)ok,owned_supplement_geometry_count++};if(owned_supplement_geometry_file){fwrite(h,sizeof(h),1,owned_supplement_geometry_file);if(ok)fwrite(data,1,h[5],owned_supplement_geometry_file);}
 if(owned_graph_live_enabled){size_t n=32+h[5],at=owned_graph_live_supplement_bytes;if(!ok||n>0x100000-at)owned_graph_live_supplement_failed=1;else if(!owned_graph_live_supplement_failed){uint8_t*next=realloc(owned_graph_live_supplement_data,at+n);if(!next)owned_graph_live_supplement_failed=1;else{memcpy(next+at,h,32);memcpy(next+at+32,data,h[5]);owned_graph_live_supplement_data=next;owned_graph_live_supplement_bytes+=n;}}}
}
static FILE*owned_supplement_file;static unsigned owned_supplement_count;
API int nf_owned_supplement_trace(const char*path){if(owned_supplement_file)fclose(owned_supplement_file);owned_supplement_file=path?fopen(path,"wb"):NULL;owned_supplement_count=0;return owned_supplement_file!=NULL;}
static void owned_supplement_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_supplement_file||owned_supplement_count>=512||pc!=0x030027f0||cpu->gprs[14]!=0x03002364||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[0],object=cpu->gprs[7],parent=cpu->gprs[1];if(!validmem(state,256)||!validmem(object,164)||!validmem(parent,16))return;
 uint8_t record[460];uint32_t h[6]={0x3150534e,c->frameCounter(c),state,object,parent,owned_supplement_count++};memcpy(record,h,24);native_read_owned(object,record+24,164);native_read_owned(parent,record+188,16);native_read_owned(state,record+204,256);fwrite(record,sizeof(record),1,owned_supplement_file);
}
static FILE*owned_region_entry_file;static unsigned owned_region_entry_count;
API int nf_owned_region_entry_trace(const char*path){if(owned_region_entry_file)fclose(owned_region_entry_file);owned_region_entry_file=path?fopen(path,"wb"):NULL;owned_region_entry_count=0;return owned_region_entry_file!=NULL;}
static void owned_region_entry_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_region_entry_file||owned_region_entry_count>=2048||pc!=0x030027f0||(!owned_graph_live_enabled&&(c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 if(!validmem(cpu->gprs[1],16)||!validmem(cpu->gprs[13],128))return;
 uint8_t record[224];uint32_t h[20]={0x3145524e,c->frameCounter(c),cpu->gprs[1],owned_region_entry_count++};memcpy(h+4,cpu->gprs,64);memcpy(record,h,80);native_read_owned(cpu->gprs[1],record+80,16);native_read_owned(cpu->gprs[13],record+96,128);fwrite(record,sizeof(record),1,owned_region_entry_file);
}
static FILE*owned_descriptor_file;static unsigned owned_descriptor_count;
API int nf_owned_descriptor_trace(const char*path){if(owned_descriptor_file)fclose(owned_descriptor_file);owned_descriptor_file=path?fopen(path,"wb"):NULL;owned_descriptor_count=0;return owned_descriptor_file!=NULL;}
static void owned_descriptor_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_descriptor_file||owned_descriptor_count>=2048||pc!=0x03001800||(!owned_graph_live_enabled&&(c->frameCounter(c)<8754||c->frameCounter(c)>8780)))return;
 unsigned state=cpu->gprs[0],desc=cpu->gprs[3];if(!validmem(state,256)||!validmem(desc,48))return;
 uint8_t record[384];uint32_t h[20]={0x3153444e,c->frameCounter(c),state,desc};memcpy(h+4,cpu->gprs,64);memcpy(record,h,80);native_read_owned(desc,record+80,48);native_read_owned(state,record+128,256);fwrite(record,sizeof(record),1,owned_descriptor_file);owned_descriptor_count++;
}
static FILE*owned_material_resolution_file;static unsigned owned_material_resolution_count;
API int nf_owned_material_resolution_trace(const char*path){if(owned_material_resolution_file)fclose(owned_material_resolution_file);owned_material_resolution_file=path?fopen(path,"wb"):NULL;owned_material_resolution_count=0;return owned_material_resolution_file!=NULL;}
static void owned_material_resolution_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_material_resolution_file||owned_material_resolution_count>=2048||pc!=0x03000304||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[1],source=cpu->gprs[6],material=cpu->gprs[0];if(!validmem(state,256)||!validmem(source,68)||!validmem(material,48))return;
 unsigned base=rd32(state+32)+rd16(source+44)*32;if(!validmem(base,32))return;unsigned animation=rd32(state+72)+rd16(base)*8;if(!validmem(animation,8))return;unsigned resolved=base+rd16(animation+2)*32;if(!validmem(resolved,32))return;
 uint32_t h[8]={0x31524d4e,c->frameCounter(c),state,source,rd32(state),base,resolved,owned_material_resolution_count++};uint8_t data[120];native_read_owned(base,data,32);native_read_owned(animation,data+32,8);native_read_owned(resolved,data+40,32);native_read_owned(material,data+72,48);fwrite(h,sizeof(h),1,owned_material_resolution_file);fwrite(data,sizeof(data),1,owned_material_resolution_file);
}
static FILE*owned_wall_owner_file;static unsigned owned_wall_owner_count;
API int nf_owned_wall_owner_trace(const char*path){if(owned_wall_owner_file)fclose(owned_wall_owner_file);owned_wall_owner_file=path?fopen(path,"wb"):NULL;owned_wall_owner_count=0;return owned_wall_owner_file!=NULL;}
static void owned_wall_owner_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_wall_owner_file||owned_wall_owner_count>=2048||pc!=0x03000304||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state=cpu->gprs[1],source=cpu->gprs[6],base=0,count=0,desc=0;if(!validmem(state,256)||!validmem(source,68))return;
 for(unsigned j=0;j<32;j++)if(native_wall_owners[j].state==state){base=native_wall_owners[j].source;count=native_wall_owners[j].count;desc=native_wall_owners[j].descriptor;break;}
 uint8_t record[484]={0};uint32_t h[16]={0x314f574e,c->frameCounter(c),state,source,base,count,desc,cpu->gprs[3],cpu->gprs[0],owned_wall_owner_count++,rd32(state+16),rd32(state+20),rd16(state+226),rd16(state+228),rd16(state+230),rd16(state+232)};memcpy(record,h,64);native_read_owned(source,record+64,68);if(validmem(desc,48))native_read_owned(desc,record+132,48);native_read_owned(rd32(state+84),record+180,48);native_read_owned(state,record+228,256);fwrite(record,sizeof(record),1,owned_wall_owner_file);
}
/* Bounded read-only clip provenance, enabled explicitly for research only. */
static FILE*owned_clip_trace_file;static unsigned owned_clip_trace_count;
static uint8_t*owned_graph_live_material_data;static size_t owned_graph_live_material_bytes;
API int nf_owned_graph_live_material_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_material_failed||!owned_graph_live_material_data)return 0;*bytes=owned_graph_live_material_bytes;if(!out)return 1;if(capacity<owned_graph_live_material_bytes)return 0;memcpy(out,owned_graph_live_material_data,owned_graph_live_material_bytes);return 1;}
static FILE*owned_graph_material_file;static uint8_t owned_graph_material_seen[65536];static unsigned owned_graph_texture_addresses[512],owned_graph_texture_sizes[512],owned_graph_texture_count;
API int nf_owned_graph_material_trace(const char*path){if(owned_graph_material_file)fclose(owned_graph_material_file);owned_graph_material_file=path?fopen(path,"wb"):NULL;return owned_graph_material_file!=NULL;}
static void owned_graph_material_capture(unsigned state,unsigned mi){
 if((!owned_graph_material_file&&!owned_graph_live_enabled)||mi==65535||owned_graph_material_seen[mi])return;owned_graph_material_seen[mi]=1;
 unsigned phase=0,shift=0,height=0,address=0,size=0,mode=0,slot=0;uint8_t sources[72]={0};uint8_t*texture=NULL;unsigned base=rd32(state+32)+mi*32;
 if(validmem(base,32)){unsigned animation=rd32(state+72)+rd16(base)*8;if(validmem(animation,8)){phase=rd16(animation+2);unsigned resolved=base+phase*32;if(validmem(resolved,32)){native_read_owned(base,sources,32);native_read_owned(animation,sources+32,8);native_read_owned(resolved,sources+40,32);shift=rd16(resolved+26);height=rd16(resolved+10);address=rd32(state)+rd32(resolved+4);if(shift<=10&&height<=1024){size=(1u<<shift)*height;if(!size)mode=3;else if(size<=0x80000&&validmem(address,size)){slot=owned_graph_texture_count;for(unsigned j=0;j<owned_graph_texture_count;j++)if(owned_graph_texture_addresses[j]==address&&owned_graph_texture_sizes[j]==size){slot=j;break;}if(slot<owned_graph_texture_count)mode=2;else if(slot<512){texture=malloc(size);if(texture&&native_read_owned(address,texture,size)){mode=1;owned_graph_texture_addresses[slot]=address;owned_graph_texture_sizes[slot]=size;owned_graph_texture_count++;}}}}}}}
 uint32_t h[12]={0x314d474e,c->frameCounter(c),state,mi,phase,shift,height,address,size,mode,slot,rd32(state)};if(owned_graph_material_file){fwrite(h,sizeof(h),1,owned_graph_material_file);fwrite(sources,1,72,owned_graph_material_file);if(mode==1)fwrite(texture,1,size,owned_graph_material_file);}
 if(owned_graph_live_enabled){size_t n=120+(mode==1?size:0);if(!mode||n>0x1000000-owned_graph_live_material_bytes)owned_graph_live_material_failed=1;else if(!owned_graph_live_material_failed){uint8_t*next=realloc(owned_graph_live_material_data,owned_graph_live_material_bytes+n);if(!next)owned_graph_live_material_failed=1;else{size_t at=owned_graph_live_material_bytes;memcpy(next+at,h,48);memcpy(next+at+48,sources,72);if(mode==1)memcpy(next+at+120,texture,size);owned_graph_live_material_data=next;owned_graph_live_material_bytes+=n;}}}free(texture);
}
static FILE*owned_object_palette_file;
API int nf_owned_object_palette_trace(const char*path){if(owned_object_palette_file)fclose(owned_object_palette_file);owned_object_palette_file=path?fopen(path,"wb"):NULL;return owned_object_palette_file!=NULL;}
static FILE*owned_object_pose_file;
API int nf_owned_object_pose_trace(const char*path){if(owned_object_pose_file)fclose(owned_object_pose_file);owned_object_pose_file=path?fopen(path,"wb"):NULL;return owned_object_pose_file!=NULL;}
static void owned_object_pose_capture(struct ARMCore*cpu){
 if(!owned_object_pose_file)return;unsigned state=cpu->gprs[6],object=cpu->gprs[7];if(!validmem(state,256)||!validmem(object,164))return;unsigned skin=c->busRead8(c,object+136),address=rd32(state+252)+skin*48;uint8_t data[260]={0};int ok=skin!=255&&validmem(address,48)&&native_read_owned(object,data,164)&&native_read_owned(rd32(state+84),data+164,48)&&native_read_owned(address,data+212,48);uint32_t h[8]={0x31504f4e,c->frameCounter(c),state,object,skin,address,260,(unsigned)ok};fwrite(h,sizeof(h),1,owned_object_pose_file);fwrite(data,sizeof(data),1,owned_object_pose_file);if(owned_object_palette_file){uint8_t palette[512];for(unsigned j=0;j<512;j++)palette[j]=c->busRead8(c,0x05000000+j);h[0]=0x314c504e;h[6]=724;fwrite(h,sizeof(h),1,owned_object_palette_file);fwrite(data,212,1,owned_object_palette_file);fwrite(palette,512,1,owned_object_palette_file);}
}
static FILE*owned_object_texture_file;static unsigned owned_object_texture_count;
API int nf_owned_object_texture_trace(const char*path){if(owned_object_texture_file)fclose(owned_object_texture_file);owned_object_texture_file=path?fopen(path,"wb"):NULL;owned_object_texture_count=0;return owned_object_texture_file!=NULL;}
static void owned_object_texture_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_object_texture_file||owned_object_texture_count>=2048||pc!=0x03002444||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 owned_object_pose_capture(cpu); unsigned state=cpu->gprs[6],object=cpu->gprs[7],sprite=cpu->gprs[4],address=rd32(cpu->gprs[13]+4);if(!validmem(state,256)||!validmem(object,164)||!validmem(sprite,32))return;unsigned shift=rd16(sprite+26),height=rd16(sprite+10),size=shift<=10&&height<=1024?(1u<<shift)*height:0,ok=0;uint8_t data[500],*texture=NULL;native_read_owned(object,data,164);native_read_owned(state,data+164,256);native_read_owned(sprite,data+420,32);native_read_owned(rd32(state+84),data+452,48);if(size&&size<=0x80000&&validmem(address,size)){texture=malloc(size);ok=texture&&native_read_owned(address,texture,size);}uint32_t h[12]={0x31544f4e,c->frameCounter(c),state,object,sprite,address,cpu->gprs[12],shift,height,ok?size:0,ok,owned_object_texture_count++};fwrite(h,sizeof(h),1,owned_object_texture_file);fwrite(data,sizeof(data),1,owned_object_texture_file);if(ok)fwrite(texture,1,size,owned_object_texture_file);free(texture);
}
static FILE*owned_graph_models_file;static uint8_t owned_graph_models_seen[32768];
API int nf_owned_graph_models_trace(const char*path){if(owned_graph_models_file)fclose(owned_graph_models_file);owned_graph_models_file=path?fopen(path,"wb"):NULL;return owned_graph_models_file!=NULL;}
static void owned_graph_models_capture(unsigned state,unsigned object){
 unsigned eligibility=rd16(object+8);if(!owned_graph_models_file||(rd16(object+10)&16)||!rd16(object+72)||!(eligibility&4||((eligibility&1)&&!(eligibility&2))))return;int id=(int16_t)rd16(object+54);if(id<=0||owned_graph_models_seen[id])return;owned_graph_models_seen[id]=1;unsigned descriptors=rd32(state+124)+(id-1)*40;int ok=validmem(descriptors,80);uint8_t data[548]={0};if(ok)ok=native_read_owned(object,data,164)&&native_read_owned(state,data+164,256)&&native_read_owned(rd32(state+84),data+420,48)&&native_read_owned(descriptors,data+468,80);uint32_t h[8]={0x314d4f4e,c->frameCounter(c),state,(unsigned)id,descriptors,object,548,(unsigned)ok};fwrite(h,sizeof(h),1,owned_graph_models_file);fwrite(data,1,sizeof(data),owned_graph_models_file);
}
static uint8_t*owned_graph_live_object_data;static size_t owned_graph_live_object_bytes;static unsigned owned_graph_live_object_failed;
API int nf_owned_graph_live_objects_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_enabled||owned_graph_live_object_failed||!owned_graph_live_object_data)return 0;*bytes=owned_graph_live_object_bytes;if(!out)return 1;if(capacity<*bytes)return 0;memcpy(out,owned_graph_live_object_data,*bytes);return 1;}
static FILE*owned_graph_objects_file;
API int nf_owned_graph_objects_trace(const char*path){if(owned_graph_objects_file)fclose(owned_graph_objects_file);owned_graph_objects_file=path?fopen(path,"wb"):NULL;return owned_graph_objects_file!=NULL;}
static void owned_graph_objects_capture(unsigned state,unsigned id,unsigned descriptor){
 if(!owned_graph_objects_file&&!owned_graph_live_enabled)return;unsigned table=rd32(state+12),head=65535,ok=1,count=0,index,base=rd32(state+60);if(validmem(table+id*2,2))head=rd16(table+id*2);else ok=0;index=head;
 uint8_t objects[512*168],sources[96];unsigned seen[512];ok=ok&&native_read_owned(rd32(state+84),sources,48)&&native_read_owned(descriptor,sources+48,48);
 while(index!=65535&&ok){if(count==512||index>65534){ok=0;break;}unsigned duplicate=0;for(unsigned j=0;j<count;j++)if(seen[j]==index)duplicate=1;if(duplicate){ok=0;break;}unsigned address=base+index*164;if(address<base||!validmem(address,164)){ok=0;break;}owned_graph_models_capture(state,address);seen[count]=index;memcpy(objects+count*168,&index,4);native_read_owned(address,objects+count*168+4,164);index=rd16(address+2);count++;}
 uint32_t h[8]={0x314f474e,c->frameCounter(c),state,id,head,count,count*168,ok};if(owned_graph_objects_file){fwrite(h,sizeof(h),1,owned_graph_objects_file);fwrite(sources,1,96,owned_graph_objects_file);fwrite(objects,168,count,owned_graph_objects_file);}
 if(owned_graph_live_enabled){size_t n=128+count*168;if(!ok||n>0x800000-owned_graph_live_object_bytes)owned_graph_live_object_failed=1;else if(!owned_graph_live_object_failed){uint8_t*next=realloc(owned_graph_live_object_data,owned_graph_live_object_bytes+n);if(!next)owned_graph_live_object_failed=1;else{size_t at=owned_graph_live_object_bytes;memcpy(next+at,h,32);memcpy(next+at+32,sources,96);memcpy(next+at+128,objects,count*168);owned_graph_live_object_data=next;owned_graph_live_object_bytes+=n;}}}
}
static uint8_t*owned_graph_live_data;static size_t owned_graph_live_bytes;static uint64_t owned_graph_build_epoch;
static uint8_t*owned_supplement_closed_data;static size_t owned_supplement_closed_bytes;
static uint8_t*owned_graph_closed_data;static size_t owned_graph_closed_bytes;static unsigned owned_graph_closed_refresh,owned_graph_closed_source;static uint64_t owned_graph_closed_epoch;
API int nf_owned_graph_live_enable(unsigned enabled){free(owned_supplement_closed_data);owned_supplement_closed_data=NULL;owned_supplement_closed_bytes=0;free(owned_graph_closed_data);owned_graph_closed_data=NULL;owned_graph_closed_bytes=0;owned_graph_closed_refresh=owned_graph_closed_source=0;owned_graph_closed_epoch=0;owned_graph_live_enabled=!!enabled;free(owned_graph_live_material_data);owned_graph_live_material_data=NULL;owned_graph_live_material_bytes=0;owned_graph_live_material_failed=0;free(owned_graph_live_callback_data);owned_graph_live_callback_data=NULL;owned_graph_live_callback_bytes=0;owned_graph_live_callback_failed=0;free(owned_graph_live_association_data);owned_graph_live_association_data=NULL;owned_graph_live_association_bytes=0;owned_graph_live_association_failed=0;free(owned_graph_live_supplement_data);owned_graph_live_supplement_data=NULL;owned_graph_live_supplement_bytes=0;owned_graph_live_supplement_failed=0;free(owned_graph_live_supplement_texture_data);owned_graph_live_supplement_texture_data=NULL;owned_graph_live_supplement_texture_bytes=0;owned_graph_live_supplement_texture_failed=0;free(owned_graph_live_object_data);owned_graph_live_object_data=NULL;owned_graph_live_object_bytes=0;owned_graph_live_object_failed=0;free(owned_graph_live_data);owned_graph_live_data=NULL;owned_graph_live_bytes=0;return 1;}
API int nf_owned_graph_live_read(void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_live_data)return 0;*bytes=owned_graph_live_bytes;if(!out)return 1;if(capacity<owned_graph_live_bytes)return 0;memcpy(out,owned_graph_live_data,owned_graph_live_bytes);return 1;}
API unsigned nf_owned_graph_closed_latest(void){return owned_graph_closed_epoch==nf_native_scene_epoch()?owned_graph_closed_refresh:0;}
API int nf_owned_graph_closed_read(uint64_t epoch,unsigned refresh,void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_graph_closed_data||epoch!=nf_native_scene_epoch()||epoch!=owned_graph_closed_epoch||refresh!=owned_graph_closed_refresh)return 0;*bytes=owned_graph_closed_bytes;if(!out)return 1;if(capacity<*bytes)return 0;memcpy(out,owned_graph_closed_data,*bytes);return 1;}
API int nf_owned_supplement_closed_read(uint64_t epoch,unsigned refresh,void*out,size_t capacity,size_t*bytes){if(!bytes||!owned_supplement_closed_data||epoch!=nf_native_scene_epoch()||epoch!=owned_graph_closed_epoch||refresh!=owned_graph_closed_refresh)return 0;*bytes=owned_supplement_closed_bytes;if(!out)return 1;if(capacity<*bytes)return 0;memcpy(out,owned_supplement_closed_data,*bytes);return 1;}
static void owned_graph_live_close(uint64_t epoch,unsigned refresh){
 if(!owned_graph_live_enabled||!owned_graph_live_data||owned_graph_live_material_failed||owned_graph_live_object_failed||owned_graph_live_callback_failed||owned_graph_live_association_failed||owned_graph_live_supplement_failed||owned_graph_live_supplement_texture_failed)return;
 unsigned source;memcpy(&source,owned_graph_live_data+4,4);if(!epoch||epoch!=owned_graph_build_epoch||source>refresh||source==owned_graph_closed_source)return;
 size_t sizes[5]={owned_graph_live_bytes,owned_graph_live_material_bytes,owned_graph_live_object_bytes,owned_graph_live_callback_bytes,owned_graph_live_association_bytes},n=40;const uint8_t*parts[5]={owned_graph_live_data,owned_graph_live_material_data,owned_graph_live_object_data,owned_graph_live_callback_data,owned_graph_live_association_data};
 for(unsigned i=0;i<5;i++){if(sizes[i]>0x2000000-n)return;n+=sizes[i];}
 uint8_t*packet=malloc(n);if(!packet)return;uint32_t h[8]={0x3143474e,1,refresh,(unsigned)sizes[0],(unsigned)sizes[1],(unsigned)sizes[2],(unsigned)sizes[3],(unsigned)sizes[4]};memcpy(packet,h,32);memcpy(packet+32,&epoch,8);size_t at=40;for(unsigned i=0;i<5;i++){if(sizes[i])memcpy(packet+at,parts[i],sizes[i]);at+=sizes[i];}
 size_t sn=32+owned_graph_live_supplement_bytes+owned_graph_live_supplement_texture_bytes;if(sn>0x1000000){free(packet);return;}uint8_t*sp=malloc(sn);if(!sp){free(packet);return;}uint32_t sh[6]={0x3143534e,1,refresh,source,(unsigned)owned_graph_live_supplement_bytes,(unsigned)owned_graph_live_supplement_texture_bytes};memcpy(sp,sh,24);memcpy(sp+24,&epoch,8);if(sh[4])memcpy(sp+32,owned_graph_live_supplement_data,sh[4]);if(sh[5])memcpy(sp+32+sh[4],owned_graph_live_supplement_texture_data,sh[5]);free(owned_supplement_closed_data);owned_supplement_closed_data=sp;owned_supplement_closed_bytes=sn;
 free(owned_graph_closed_data);owned_graph_closed_data=packet;owned_graph_closed_bytes=n;owned_graph_closed_epoch=epoch;owned_graph_closed_refresh=refresh;owned_graph_closed_source=source;
}
static FILE*owned_graph_snapshot_file;
API int nf_owned_graph_snapshot_trace(const char*path){if(owned_graph_snapshot_file)fclose(owned_graph_snapshot_file);owned_graph_snapshot_file=path?fopen(path,"wb"):NULL;return owned_graph_snapshot_file!=NULL;}
static FILE*owned_graph_file;static unsigned owned_graph_refresh;
API int nf_owned_graph_trace(const char*path){if(owned_graph_file)fclose(owned_graph_file);owned_graph_file=path?fopen(path,"wb"):NULL;owned_graph_refresh=0;return owned_graph_file!=NULL;}
static void owned_graph_capture(struct ARMCore*cpu,unsigned pc){
 if((!owned_graph_file&&!owned_graph_live_enabled)||pc!=0x03002b74||(!owned_graph_live_enabled&&(c->frameCounter(c)<8754||c->frameCounter(c)>8780))||owned_graph_refresh==c->frameCounter(c))return;
 unsigned state=cpu->gprs[0],root=cpu->gprs[1];if(!validmem(state,256)||rd16(cpu->gprs[3]+12)!=0)return;
 if(owned_graph_live_enabled){owned_graph_build_epoch=nf_native_scene_epoch();free(owned_graph_live_material_data);owned_graph_live_material_data=NULL;owned_graph_live_material_bytes=0;owned_graph_live_material_failed=0;free(owned_graph_live_callback_data);owned_graph_live_callback_data=NULL;owned_graph_live_callback_bytes=0;owned_graph_live_callback_failed=0;free(owned_graph_live_association_data);owned_graph_live_association_data=NULL;owned_graph_live_association_bytes=0;owned_graph_live_association_failed=0;free(owned_graph_live_supplement_data);owned_graph_live_supplement_data=NULL;owned_graph_live_supplement_bytes=0;owned_graph_live_supplement_failed=0;free(owned_graph_live_supplement_texture_data);owned_graph_live_supplement_texture_data=NULL;owned_graph_live_supplement_texture_bytes=0;owned_graph_live_supplement_texture_failed=0;free(owned_graph_live_object_data);owned_graph_live_object_data=NULL;owned_graph_live_object_bytes=0;owned_graph_live_object_failed=0;}
 memset(owned_graph_models_seen,0,sizeof(owned_graph_models_seen));
 memset(owned_graph_material_seen,0,sizeof(owned_graph_material_seen));owned_graph_texture_count=0;
 uint16_t queue[4096];uint8_t seen[65536]={0};unsigned count=1,cursor=0,used=0,ok=1;queue[0]=root;seen[root&65535]=1;
 uint8_t*data=malloc(4096u*(16+48+32*68)),*offsets=malloc(4096u*32*32);unsigned offsets_used=0;if(!data||!offsets){free(data);free(offsets);return;}
 while(cursor<count&&ok){unsigned id=queue[cursor++],desc=rd32(state+20)+id*48;if(!validmem(desc,48)){ok=0;break;}unsigned n=rd16(desc+2),points=rd32(state+16)+rd16(desc)*68;if(!n||n>32||!validmem(points,n*68)){ok=0;break;}
 owned_graph_objects_capture(state,id,desc);
 owned_graph_material_capture(state,rd16(desc+4));owned_graph_material_capture(state,rd16(desc+8));for(unsigned j=0;j<n;j++)owned_graph_material_capture(state,rd16(points+j*68+44));
 for(unsigned j=0;j<n&&ok;j++){unsigned oi=rd16(points+j*68+42);memset(offsets+offsets_used,0,32);if(oi!=65535)ok=native_read_owned(rd32(state+24)+oi*32,offsets+offsets_used,32);offsets_used+=32;}
 uint32_t h[4]={id,n,desc,points};memcpy(data+used,h,16);used+=16;native_read_owned(desc,data+used,48);used+=48;native_read_owned(points,data+used,n*68);
 for(unsigned i=0;i<n;i++){unsigned link=rd16(points+i*68+48);if(link!=65535&&!seen[link]){if(count==4096){ok=0;break;}seen[link]=1;queue[count++]=link;}}used+=n*68;
 }
 uint32_t h[8]={0x3147504e,c->frameCounter(c),state,root,count,used,ok,0};if(owned_graph_file){fwrite(h,sizeof(h),1,owned_graph_file);if(ok)fwrite(data,1,used,owned_graph_file);}if(owned_graph_snapshot_file||owned_graph_live_enabled){uint8_t context[896];int complete=ok&&(!owned_graph_live_enabled||(!owned_graph_live_material_failed&&!owned_graph_live_object_failed))&&native_read_owned(state,context,256)&&native_read_owned(rd32(state+84),context+256,48)&&native_read_owned(rd32(state+80),context+304,64)&&native_read_owned(cpu->gprs[3],context+368,16);for(unsigned j=0;j<512;j++)context[384+j]=c->busRead8(c,0x05000000+j);uint32_t sh[8]={0x3253474e,c->frameCounter(c),root,count,used,offsets_used,(unsigned)complete,state};if(owned_graph_snapshot_file){fwrite(sh,sizeof(sh),1,owned_graph_snapshot_file);if(complete){fwrite(context,1,896,owned_graph_snapshot_file);fwrite(data,1,used,owned_graph_snapshot_file);fwrite(offsets,1,offsets_used,owned_graph_snapshot_file);}}
 if(owned_graph_live_enabled){free(owned_graph_live_data);owned_graph_live_data=NULL;owned_graph_live_bytes=0;if(complete){size_t n=32+896+used+offsets_used;uint8_t*packet=malloc(n);if(packet){memcpy(packet,sh,32);memcpy(packet+32,context,896);memcpy(packet+928,data,used);memcpy(packet+928+used,offsets,offsets_used);owned_graph_live_data=packet;owned_graph_live_bytes=n;}}}}free(offsets);free(data);owned_graph_refresh=c->frameCounter(c);
}
static FILE*owned_traversal_file;static unsigned owned_traversal_count,owned_traversal_valid,owned_traversal_output;
API int nf_owned_traversal_trace(const char*path){if(owned_traversal_file)fclose(owned_traversal_file);owned_traversal_file=path?fopen(path,"wb"):NULL;owned_traversal_count=owned_traversal_valid=0;return owned_traversal_file!=NULL;}
static void owned_traversal_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_traversal_file||owned_traversal_count>=512||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 if(pc==0x03002b74){unsigned state=cpu->gprs[0],index=cpu->gprs[1],parent=cpu->gprs[3],outptr=cpu->gprs[2];if(!validmem(state,256)||!validmem(parent,16)||!validmem(outptr,4))return;
 unsigned desc=rd32(state+20)+index*48,count=rd16(desc+2),points=rd32(state+16)+rd16(desc)*68,matrix=rd32(state+84),fb=rd32(state+80);if(count>32||!validmem(desc,48)||!validmem(points,count*68)||!validmem(matrix,48)||!validmem(fb,64))return;
 uint32_t h[12]={0x3156544e,1,c->frameCounter(c),owned_traversal_count++,state,index,parent,rd32(outptr),rd32(cpu->gprs[13]+4),count,points,0};uint8_t payload[2608];native_read_owned(state,payload,256);native_read_owned(desc,payload+256,48);native_read_owned(matrix,payload+304,48);native_read_owned(fb,payload+352,64);native_read_owned(parent,payload+416,16);native_read_owned(points,payload+432,count*68);fwrite(h,sizeof(h),1,owned_traversal_file);fwrite(payload,1,432+count*68,owned_traversal_file);owned_traversal_output=h[7];owned_traversal_valid=1;
 }else if(pc==0x03002f70&&owned_traversal_valid){unsigned count=rd32(cpu->gprs[13]+0x60),bytes=cpu->gprs[7]-owned_traversal_output;if(bytes<=512&&bytes%16==0&&validmem(owned_traversal_output,bytes)){uint32_t h[12]={0x3156544e,2,c->frameCounter(c),owned_traversal_count-1,bytes/16,bytes};uint8_t payload[512];native_read_owned(owned_traversal_output,payload,bytes);fwrite(h,sizeof(h),1,owned_traversal_file);fwrite(payload,1,bytes,owned_traversal_file);}owned_traversal_valid=0;}
}
static FILE*owned_portal_file;static unsigned owned_portal_count;
static FILE*owned_projected_file;static uint8_t owned_projected_pending[368];static unsigned owned_projected_valid;
API int nf_owned_projected_trace(const char*path){if(owned_projected_file)fclose(owned_projected_file);owned_projected_file=path?fopen(path,"wb"):NULL;owned_projected_valid=0;return owned_projected_file!=NULL;}

API int nf_owned_portal_trace(const char*path){if(owned_portal_file)fclose(owned_portal_file);owned_portal_file=path?fopen(path,"wb"):NULL;owned_portal_count=0;return owned_portal_file!=NULL;}
static void owned_portal_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_portal_file||owned_portal_count>=2048||pc!=0x03002d20||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned sp=cpu->gprs[13],state=cpu->gprs[9],point=rd32(sp+0x10),next=rd32(sp)<rd32(sp+0x14)?point+68:rd32(sp+0x18),matrix=rd32(state+0x54),fb=rd32(state+0x50);
 if(!validmem(point,68)||!validmem(next,68)||!validmem(matrix,48)||!validmem(fb,64))return;
 uint8_t record[344]={0};uint32_t header[8]={0x3154504e,c->frameCounter(c),state,point,next,matrix,fb,owned_portal_count++};memcpy(record,header,32);native_read_owned(point,record+32,68);native_read_owned(next,record+100,68);native_read_owned(matrix,record+168,48);native_read_owned(fb,record+216,64);memcpy(record+280,cpu->gprs,64);fwrite(record,sizeof(record),1,owned_portal_file);if(owned_projected_file){memcpy(owned_projected_pending,record,344);owned_projected_valid=1;}
}
static FILE*owned_partition_file;static uint32_t owned_partition_pending[24];static unsigned owned_partition_count,owned_partition_valid;
API int nf_owned_partition_trace(const char*path){if(owned_partition_file)fclose(owned_partition_file);owned_partition_file=path?fopen(path,"wb"):NULL;owned_partition_count=owned_partition_valid=0;return owned_partition_file!=NULL;}
static void owned_partition_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_partition_file||owned_partition_count>=2048||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 if(pc==0x03002e44){unsigned sp=cpu->gprs[13],state=cpu->gprs[9],parent=rd32(sp+0x38),point=rd32(sp+0x10);if(!validmem(parent,16)||!validmem(point,68)||!validmem(state,256))return;
 uint32_t v[20]={0x3150434e,c->frameCounter(c),state,point,cpu->gprs[5],cpu->gprs[6],rd32(sp+4),rd16(parent+2),rd16(parent+4),rd16(parent+10),rd16(parent+12),rd16(state+0x5c),rd16(state+0x5e),rd32(sp+0xc),rd16(point+0x2e),cpu->gprs[8],cpu->gprs[10],parent,cpu->gprs[7],0};memcpy(owned_partition_pending,v,sizeof(v));owned_partition_valid=1;
 }else if(pc==0x03002f14&&owned_partition_valid){unsigned out=cpu->gprs[7];if(out==owned_partition_pending[18]&&validmem(out,16)){native_read_owned(out,(uint8_t*)(owned_partition_pending+20),16);fwrite(owned_partition_pending,sizeof(owned_partition_pending),1,owned_partition_file);owned_partition_count++;}owned_partition_valid=0;}
}

API int nf_owned_clip_trace(const char*path){if(owned_clip_trace_file)fclose(owned_clip_trace_file);owned_clip_trace_file=path?fopen(path,"wb"):NULL;owned_clip_trace_count=0;return owned_clip_trace_file!=NULL;}
static void owned_clip_trace(struct ARMCore*cpu,unsigned pc){
 if(!owned_clip_trace_file||owned_clip_trace_count>=4096||c->frameCounter(c)<8754||c->frameCounter(c)>8780)return;
 unsigned state,source;
 if(pc==0x030022dc){state=cpu->gprs[6];source=rd32(cpu->gprs[13]+0x24);}
 else if(pc==0x0300289c){state=cpu->gprs[5];source=cpu->gprs[6];}
 else if(pc==0x03002c20){state=cpu->gprs[9];source=rd32(cpu->gprs[13]+0x38);}
 else return;
 if(!validmem(state,256)||!validmem(source,16))return;
 uint32_t record[26]={0x314c434e,pc,c->frameCounter(c),state,source,owned_clip_trace_count++};memcpy(record+6,cpu->gprs,64);
 native_read_owned(source,(uint8_t*)(record+22),16);fwrite(record,sizeof(record),1,owned_clip_trace_file);
}
static __attribute__((noinline)) void world_trace_detail(struct ARMCore*cpu,unsigned pc){
 if(owned_projected_file&&owned_projected_valid&&pc==0x03002e18){unsigned sp=cpu->gprs[13];uint32_t out[6]={cpu->gprs[5],cpu->gprs[6],rd32(sp+4),cpu->gprs[10],cpu->gprs[8],rd32(sp+0x64)};memcpy(owned_projected_pending+344,out,24);fwrite(owned_projected_pending,368,1,owned_projected_file);owned_projected_valid=0;}
 owned_object_texture_trace(cpu,pc);
 owned_input_list_trace(cpu,pc);
 owned_eligibility_trace(cpu,pc);
 owned_filter_trace(cpu,pc);
 owned_association_trace(cpu,pc);
 owned_chain_trace(cpu,pc);
 owned_supplement_textures_trace(cpu,pc);
 owned_supplement_geometry_trace(cpu,pc);
 owned_supplement_trace(cpu,pc);
 owned_region_entry_trace(cpu,pc);
 owned_descriptor_trace(cpu,pc);
 owned_material_resolution_trace(cpu,pc);
 owned_wall_owner_trace(cpu,pc);
 owned_graph_capture(cpu,pc);
 owned_traversal_trace(cpu,pc);
 owned_portal_trace(cpu,pc);
 owned_partition_trace(cpu,pc);
 owned_clip_trace(cpu,pc);
 if(!world_file){if(world_native_capture)world_native_after_limit(cpu,pc);return;}
 if(world_events>=world_event_limit){world_native_after_limit(cpu,pc);return;}
 if(initial_writes_enabled&&!initial_surface_seen&&(pc==0x030032f0||pc==0x03000304||pc==0x03004770)){
  initial_surface_seen=1;
  uint32_t header[21]={0x3157464e,0xffff0093,c->frameCounter(c),world_events++,2};memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  uint32_t block[3]={93,0,initial_write_count*28};fwrite(block,sizeof(block),1,world_file);fwrite(initial_writes,28,initial_write_count,world_file);
  uint32_t overflow[3]={94,0,4};fwrite(overflow,sizeof(overflow),1,world_file);fwrite(&initial_write_overflow,4,1,world_file);
 }
 /* Original initialization inputs: optional, bounded, read-only. */
 if(initial_writes_enabled&&!initial_surface_seen&&(pc==0x030002c0||pc==0x03003814)){
  unsigned source_size=0,source=cpu->gprs[1],sp=cpu->gprs[13];
  if(pc==0x03003814&&validmem(sp,8)){
   unsigned stride=rd32(sp),rows=cpu->gprs[3];
   unsigned width=(cpu->gprs[2]>>5)*32;
   if(rows>0&&rows<=512&&stride<=4096&&width<=4096){
    uint64_t extent=(uint64_t)stride*(rows-1)+width+32;
    if(extent<=0x40000&&validmem(source,(unsigned)extent))source_size=(unsigned)extent;
   }
  }
  uint32_t header[21]={0x3157464e,0xffff0095,c->frameCounter(c),world_events++,pc==0x03003814?3:1};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  uint32_t metadata[3]={pc,source_size,rd16(0x04000000)},block[3]={95,0,sizeof(metadata)};
  fwrite(block,sizeof(block),1,world_file);fwrite(metadata,sizeof(metadata),1,world_file);
  if(pc==0x03003814){world_block(96,sp,8);world_block(97,source,source_size);}
 }
 if(sprite_writes_enabled&&pc==0x03000298&&cpu->gprs[0]>=0x06014000&&cpu->gprs[0]<0x06018000){
  unsigned bytes=(cpu->gprs[2]>>5)*32;
  if(bytes<=0x4000&&validmem(cpu->gprs[1],bytes)){
   uint32_t header[21]={0x3157464e,0xffff0102,c->frameCounter(c),world_events++,1};
   memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
   world_block(102,cpu->gprs[1],bytes);
  }
 }
 if(native_live_scene&&(pc==0x030002c0||pc==0x03003814||pc==0x03000298)&&cpu->gprs[0]>=0x06000000&&cpu->gprs[0]<0x06018000){
  uint32_t commands[5]={cpu->gprs[0]-0x06000000,cpu->gprs[2],cpu->gprs[3],0,0};
  if(pc==0x030002c0){commands[1]=cpu->gprs[1];commands[2]=cpu->gprs[2];native_live_submit(4,commands,1,0,0,0,0);}
  else if(pc==0x03000298)native_live_submit(6,commands,1,0,cpu->gprs[1],(cpu->gprs[2]>>5)*32,0);
  else {commands[3]=rd32(cpu->gprs[13]);commands[4]=rd32(cpu->gprs[13]+4);unsigned rows=commands[2],bytes=rows?((rows-1)*(commands[3]&~1u)+((commands[1]>>5)+1)*32):0;native_live_submit(5,commands,1,0,cpu->gprs[1],bytes,0);}
 }
 world_framebuffer_trace(cpu,pc);
 if(world_framebuffer_enabled&&world_framebuffer_pending_count&&pc==0x03003d4c){
  unsigned poly=cpu->gprs[4],rectangle=rd32(cpu->gprs[5]+4);
  if(!validmem(poly,32)||!validmem(rectangle,16))return;
  unsigned count=rd32(poly+20),indices=rd32(poly+8),points=rd32(poly),max_index=0;
  if(count<3||count>32||!validmem(indices,count*2))return;
  for(unsigned i=0;i<count;i++){unsigned index=rd16(indices+i*2);if(index>max_index)max_index=index;}
  if(max_index>=2048||!validmem(points,(max_index+1)*4))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,4};memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(86,rectangle,16);world_block(87,poly,32);world_block(88,indices,count*2);world_block(89,points,(max_index+1)*4);return;
 }
 if(pc==0x03005920){
  const char* enabled=getenv("NF_TRACE_MODEL_SPANS");
  if(!enabled||strcmp(enabled,"1"))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,1};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  uint32_t values[5];
  for(unsigned i=0;i<5;i++)values[i]=rd32(rd32(0x03005a30+i*4));
  uint32_t block[3]={91,0,sizeof(values)};
  fwrite(block,sizeof(block),1,world_file);fwrite(values,sizeof(values),1,world_file);return;
 }
 if(pc==0x03005320||pc==0x030053e8){
  if(!validmem(cpu->gprs[0],68))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,1};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(75,cpu->gprs[0],68);
  return;
 }
 if(pc==0x08023448){
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,3};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(81,cpu->gprs[7]+0x140,36);
  world_block(82,cpu->gprs[8],164);world_block(83,cpu->gprs[5],48);
  return;
 }
 if(pc==0x0806db14||pc==0x0806dc5c){
  if(!validmem(cpu->gprs[2],48))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,3};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(71,pc==0x0806db14?cpu->gprs[0]:0,48);
  world_block(72,pc==0x0806db14?cpu->gprs[1]:0,48);
  world_block(73,cpu->gprs[2],48);
  return;
 }
 if(pc==0x03002628){
  unsigned state=cpu->gprs[6],object=cpu->gprs[7],context=cpu->gprs[0];
  if(!validmem(state,256)||!validmem(object,164)||!validmem(context,68))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,4};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(61,state,256);world_block(62,object,164);
  world_block(63,rd32(state+0x54),48);world_block(64,context,68);
  return;
 }
 if(pc==0x030045e0||pc==0x03004770){
  unsigned context=cpu->gprs[pc==0x030045e0?0:4];
  if(!validmem(context,68))return;
  unsigned descriptor=rd32(context+12);
  if(!validmem(descriptor,40))return;
  unsigned count=rd16(descriptor+36),source=rd32(context+16)+rd32(descriptor)*6;
  if(count>2048)return;
  unsigned faces=rd16(descriptor+34),face_sizes=rd32(context+44)+rd32(descriptor+28);
  unsigned indices=0;
  if(faces>512||!validmem(face_sizes,faces))return;
  for(unsigned i=0;i<faces;i++){unsigned n=c->busRead8(c,face_sizes+i);if(n<3||n>32)return;indices+=n;}
  if(indices>4096)return;
  unsigned vertex_indices=rd32(context+32)+rd32(descriptor+4)*2;
  unsigned uv_indices=rd32(context+36)+rd32(descriptor+24)*2,max_uv=0;
  if(!validmem(vertex_indices,indices*2)||!validmem(uv_indices,indices*2))return;
  for(unsigned i=0;i<indices;i++){unsigned index=rd16(uv_indices+i*2);if(index>max_uv)max_uv=index;}
  if(max_uv>4095)return;
  unsigned uv=rd32(context+20);
  if(rd16(descriptor+32)&1)uv+=rd32(descriptor+8)*4;
  unsigned shift=rd16(context+56),height=rd16(context+58);
  unsigned texture_size=shift<=10&&height<=1024?(1u<<shift)*height:0;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,15};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  world_block(51,context,68);world_block(52,descriptor,40);
  world_block(53,rd32(context+60),48);world_block(54,source,count*6);
  world_block(55,rd32(context+48),count*4);world_block(56,rd32(context+8),64);
  world_block(57,cpu->gprs[13],128);
  world_block(58,vertex_indices,indices*2);world_block(59,uv_indices,indices*2);
  world_block(60,face_sizes,faces);world_block(65,uv,(max_uv+1)*4);
  world_block(66,rd32(context+52),texture_size);world_block(67,0x05000000,512);
  world_block(68,rd32(context+48),count*4);
  /* Owned per-draw rectangle; do not infer it from later RAM snapshots. */
  unsigned frame_context=rd32(context+8);
  world_block(90,validmem(frame_context,8)?rd32(frame_context+4):0,16);
#ifdef NF_VISIBILITY_CAPTURE
  if(pc==0x03004770){unsigned addresses[10]={context,descriptor,rd32(context+60),frame_context,source,face_sizes,vertex_indices,uv_indices,uv,rd32(frame_context+4)};unsigned sizes[10]={68,40,48,64,count*6,faces,indices*2,indices*2,(max_uv+1)*4,16};native_model_plan_capture(context,addresses,sizes);}
#endif

  return;
 }
 if(pc==0x03000304){
  unsigned material=cpu->gprs[0],state=cpu->gprs[1],source=cpu->gprs[6];
  if(!validmem(material,48)||!validmem(state,256)||!validmem(source,68))return;
  uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,15};
  memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
  native_wall_plan_capture(material,state,cpu->gprs[3],source,cpu->gprs[2]);
  world_block(1,state,256);world_block(2,rd32(state+0x54),48);
  world_block(3,rd32(state+0x50),64);
  world_block(4,cpu->gprs[3],32); /* Resolved wall texture descriptor. */
  world_block(5,source,68);world_block(6,rd32(material+12),52);
  world_block(7,rd32(state+0x68),32*52);world_block(8,material,48);
  unsigned index=rd16(source+42);
  world_block(9,index!=65535?rd32(state+24)+index*32:0,32);
  unsigned shift=rd16(material+36),height=rd16(material+38);
  unsigned size=shift<=10&&height<=1024?(1u<<shift)*height:0;
  world_block(66,rd32(material+40),size);world_block(67,0x05000000,512);
  world_block(70,rd32(state+72)+rd16(cpu->gprs[3])*8,8);
  /* The wall span indexes this palette-remap table by texel*16 + shade. */
  unsigned wall_context=rd32(material+8);
  world_block(74,validmem(wall_context,24)?rd32(wall_context+20):0,256*16);
  unsigned base_material=rd32(state+32)+rd16(source+44)*32;
  world_block(77,base_material,32);
  world_block(78,validmem(base_material,32)?rd32(state+72)+rd16(base_material)*8:0,8);
  return;
 }
 if(pc!=0x03000d48&&pc!=0x03001800&&pc!=0x03002964&&pc!=0x030032f0)return;
 unsigned state=pc==0x030032f0?cpu->gprs[1]:pc==0x03002964?cpu->gprs[5]:cpu->gprs[0];
 if(!validmem(state,256))return;
 unsigned descriptor=pc==0x03000d48?cpu->gprs[1]:pc==0x03001800?cpu->gprs[3]:cpu->gprs[7];
 if(!validmem(descriptor,48))return;
 unsigned count=rd16(descriptor+2);
 if(!count||count>32)return;
 unsigned source=rd32(state+16)+rd16(descriptor)*68;
 if(pc==0x03001800){unsigned slot=32;for(unsigned j=0;j<32;j++)if(native_wall_owners[j].state==state){slot=j;break;}
  if(slot==32)for(unsigned j=0;j<32;j++)if(!native_wall_owners[j].state){slot=j;break;}
  if(slot==32)slot=(state>>2)%32;native_wall_owners[slot].state=state;native_wall_owners[slot].source=source;native_wall_owners[slot].count=count;native_wall_owners[slot].descriptor=descriptor;}
 const char*edge_animations=getenv("NF_TRACE_ROAD_EDGE_ANIMATIONS");
 unsigned capture_edge_animations=pc==0x03001800&&count<=16&&edge_animations&&!strcmp(edge_animations,"1");
 uint32_t header[21]={0x3157464e,pc,c->frameCounter(c),world_events++,10+count+(pc==0x030032f0?3:0)+(capture_edge_animations?count:0)};
 memcpy(header+5,cpu->gprs,64);fwrite(header,sizeof(header),1,world_file);
 world_block(1,state,256);
 world_block(2,rd32(state+0x54),48);
 world_block(3,rd32(state+0x50),64);
 world_block(4,descriptor,48);
 world_block(5,source,count*68);
 world_block(6,rd32(state+0x68),count*52);
 world_block(7,rd32(state+0x6c),64*24);
 world_block(8,pc==0x030032f0?cpu->gprs[0]:0,48);
 world_block(9,pc==0x030032f0?cpu->gprs[2]:0,64);
 if(capture_edge_animations)for(unsigned i=0;i<count;i++){
  unsigned material=rd32(state+0x20)+rd16(source+i*68+0x2c)*32;
  unsigned address=validmem(material,32)?rd32(state+0x48)+rd16(material)*8:0;
  world_block(100+i,address,8);
 }
 /* Preserve point and face offsets without dumping unrelated ROM assets. */
 for(unsigned i=0;i<count;i++){
  unsigned index=i<count&&validmem(source,count*68)?rd16(source+i*68+42):65535;
  world_block(10+i,index!=65535?rd32(state+24)+index*32:0,32);
 }
 unsigned face_offset=rd16(descriptor+10);
 world_block(42,face_offset!=65535?rd32(state+28)+face_offset*20:0,20);
 if(pc==0x030032f0){
  unsigned material=cpu->gprs[0],shift=rd16(material+36),height=rd16(material+38);
  unsigned size=shift<=10&&height<=1024?(1u<<shift)*height:0;
  world_block(66,rd32(material+40),size);world_block(67,0x05000000,512);
  world_block(69,cpu->gprs[13],8);
  native_road_plan_capture(material,state,descriptor,source,count,cpu->gprs[2],cpu->gprs[13]);
 }
}
/* Raw capture handlers consume registers only at explicit source PCs.
   Keep diagnostic world tracing unrestricted; fast reject other fileless calls. */
static void world_trace(struct ARMCore*cpu,unsigned pc){
 if(!world_file){switch(pc){
 case 0x03000298:
 case 0x030002c0:
 case 0x03000304:
 case 0x03000d48:
 case 0x03001800:
 case 0x03002000:
 case 0x03002044:
 case 0x03002090:
 case 0x030020f0:
 case 0x0300220c:
 case 0x030022dc:
 case 0x03002444:
 case 0x03002628:
 case 0x030027f0:
 case 0x0300289c:
 case 0x03002964:
 case 0x03002b74:
 case 0x03002c20:
 case 0x03002d20:
 case 0x03002e18:
 case 0x03002e44:
 case 0x03002f14:
 case 0x03002f70:
 case 0x030032f0:
 case 0x03003814:
 case 0x03003d24:
 case 0x03003d4c:
 case 0x030045e0:
 case 0x03004770:
 case 0x030048b0:
 case 0x03005320:
 case 0x030053e8:
 case 0x030054a0:
 case 0x03005920:
 case 0x08023448:
 case 0x0806db14:
 case 0x0806dc5c:
 break;default:return;}}
 world_trace_detail(cpu,pc);
}
API int nf_world_trace(const char*path){
 if(world_file)fclose(world_file);
 world_native_capture=path&&c&&!*path;
 world_file=path&&c&&*path?fopen(path,"wb"):NULL;world_events=0;
 const char* sprite_writes=getenv("NF_TRACE_SPRITE_WRITES");sprite_writes_enabled=world_file&&sprite_writes&&!strcmp(sprite_writes,"1");sprite_write_count=sprite_write_overflow=0;
 const char* initial=getenv("NF_TRACE_INITIAL_WRITE_PCS");initial_writes_enabled=world_file&&initial&&!strcmp(initial,"1");initial_surface_seen=initial_write_count=initial_write_overflow=0;
 const char*framebuffer=getenv("NF_TRACE_DRAW_FRAMEBUFFER");world_framebuffer_enabled=world_file&&framebuffer&&!strcmp(framebuffer,"1");world_framebuffer_draws=world_framebuffer_pending_count=0;
 world_thumb=(world_file||world_native_capture)?world_trace:NULL;
 nfsThumbTrace=(native_scene_thumb||native_model_thumb||world_thumb||calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;
 /* This capture uses the existing read-only scene hook. */
 if(world_file||world_native_capture)nf_scene_enable(1);
 return world_file!=NULL||world_native_capture;
}
