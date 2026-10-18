int nf_android_observer_sky_enable(int);
#include "camera/wall_history_store.h"
#include "camera/write_ownership.h"
#include "camera/road_history_store.h"
int nf_android_observer_wall_history_enable(int);
static void android_wall_boundary(int);
static void android_wall_close_owner(uint64_t,const NFScenePacket*);
static int android_source_world;
static uint8_t*android_previous;static size_t android_previous_bytes;
static uint64_t android_previous_epoch,android_previous_generation,android_previous_version;
static void android_previous_clear(void){free(android_previous);android_previous=NULL;android_previous_bytes=0;android_previous_epoch=android_previous_generation=android_previous_version=0;}
static int android_layers;
static uint64_t android_packet_generation,android_packet_audit_version;
static uint8_t*android_packet;static size_t android_packet_bytes;static uint64_t android_packet_epoch;
static int android_sink(void*context,uint64_t epoch,const void*data,size_t bytes){
 (void)context;NFScenePacket view;
 if(!nf_scene_packet_view(data,bytes,&view))return 0;
 android_wall_close_owner(epoch,&view);
 void*copy=malloc(bytes);if(!copy)return 0;memcpy(copy,data,bytes);
 android_previous_clear();
 if(android_packet&&android_packet_epoch==epoch){android_previous=android_packet;android_previous_bytes=android_packet_bytes;android_previous_epoch=android_packet_epoch;android_previous_generation=android_packet_generation;android_previous_version=android_packet_audit_version;android_packet=NULL;}
 uint64_t generation[2];
 android_packet_audit_version=0;
 if(android_layers&&nf_page_write_audit_generation_copy(generation)){android_packet_generation=generation[view.page];android_packet_audit_version=nf_page_write_audit_version();}
 free(android_packet);android_packet=copy;android_packet_bytes=bytes;android_packet_epoch=epoch;return 1;
}
int nf_android_observer_attach(struct mCore*core,uint32_t*framebuffer){
 if(c||!core||!framebuffer||nfsArmHook||nfsThumbTrace||nfsThumbGate)return 0;
 c=core;pixels=framebuffer;mode60=0;native_enabled=0;dt_percent=100;normalize_steering=0;
 nf_page_write_audit_enable(0);
@INSTALL_ORIGINAL_HOOKS@
 if(!nf_native_scene_sink(android_sink,NULL))return 0;
 if(!nf_native_scene_multimodel(1))return 0;
 return 1;
}
void nf_android_observer_detach(void){
 if(!c)return;
 nf_android_observer_sky_enable(0);nf_android_observer_wall_history_enable(0);
 struct ARMCore*cpu=c->cpu;
 cpu->memory.store16=old16;cpu->memory.store32=old32;cpu->memory.store8=old8;cpu->memory.storeMultiple=oldMultiple;
 struct GBAVideoRenderer*r=((struct GBA*)c->board)->video.renderer;r->drawScanline=original_scanline;
#ifdef NF_VISIBILITY_CAPTURE
 if(layer_dirty_enabled){r->writeVRAM=layer_old_vram;r->writePalette=layer_old_palette;r->writeOAM=layer_old_oam;}
#endif
 android_source_world=0;android_layers=0;nf_layer_queue_enable(0);
 nf_scene_enable(0);nf_close();android_previous_clear();free(android_packet);android_packet=NULL;android_packet_bytes=0;android_packet_epoch=0;
}
void nf_android_observer_boundary(void){if(c){native_scene_check_mode();android_wall_boundary(0);}}
void nf_android_observer_reset(void){
 if(!c)return;android_previous_clear();nf_scene_reset();nf_native_scene_discontinuity();android_wall_boundary(1);
 if(android_layers)nf_layer_queue_enable(1);
 free(android_packet);android_packet=NULL;android_packet_bytes=0;android_packet_epoch=0;
}
size_t nf_android_observer_copy(void*out,size_t capacity){
 if(!c||!android_packet||android_packet_epoch!=nf_native_scene_epoch())return 0;
 if(!out)return android_packet_bytes;
 if(capacity<android_packet_bytes)return 0;memcpy(out,android_packet,android_packet_bytes);return android_packet_bytes;
}
void nf_android_observer_stats(uint64_t out[8]){
 uint32_t s[4]={0};nf_native_scene_stats(s);
 uint64_t values[8]={c!=NULL,nf_native_scene_epoch(),s[0],s[1],s[2],s[3],nf_android_observer_copy(NULL,0),0};
 if(android_packet&&android_packet_epoch==nf_native_scene_epoch()){NFScenePacket p;if(nf_scene_packet_view(android_packet,android_packet_bytes,&p))values[7]=p.serial;}
 memcpy(out,values,sizeof(values));
}

/* Auxiliary capture is opt-in and keeps the original scanline-owned state.
   A refresh is not claimed to belong to a geometry packet by this interface. */
int nf_android_observer_layers(int enabled){
 if(!c||!nf_layer_queue_enable(enabled!=0))return 0;
 android_layers=enabled!=0;nf_page_write_audit_enable(android_layers);
 nf_page_write_audit_generation_reset();android_packet_audit_version=0;android_previous_clear();return 1;
}
int nf_android_observer_layer_info(uint64_t out[5]){
 if(!c||!android_layers||!out)return 0;
 unsigned refresh=nf_layer_queue_latest();uint32_t context[3];
 uint64_t epoch=nf_native_scene_epoch();
 if(!nf_layer_queue_context(epoch,refresh,context))return 0;
 uint64_t info[5]={epoch,refresh,context[0],context[1],context[2]};
 memcpy(out,info,sizeof(info));return 1;
}
size_t nf_android_observer_layer_row(uint64_t epoch,unsigned refresh,unsigned row,void*out,size_t capacity){
 if(!c||!android_layers||row>=160||epoch!=nf_native_scene_epoch())return 0;
 uint32_t context[3];if(!nf_layer_queue_context(epoch,refresh,context))return 0;
 size_t bytes=sizeof(NFHardwareLayerRow);if(!out)return bytes;
 if(capacity<bytes)return 0;
 return nf_layer_queue_row(epoch,refresh,row,out,(unsigned)bytes)?bytes:0;
}

/* Strict whole-scanout join. Transitional/split pages are deliberately rejected;
   split-scene support must carry two explicit owners rather than guess. */
int nf_android_observer_pair(unsigned refresh,uint64_t out[8]){
 if(!c||!android_layers||!out||!android_packet_audit_version||!nf_android_observer_copy(NULL,0))return 0;
 if(android_packet_audit_version!=nf_page_write_audit_version())return 0;
 NFScenePacket packet;uint64_t generation;
 if(!nf_scene_packet_view(android_packet,android_packet_bytes,&packet)||refresh<=packet.end_refresh)return 0;
 if(!nf_layer_queue_page_generation(android_packet_epoch,refresh,packet.page,&generation)||generation!=android_packet_generation)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==android_packet_epoch&&layer_queue[i].refresh==refresh){
  if(!layer_queue[i].kind||!nf_layer_snapshot_display_page(layer_queue[i].snapshot,packet.page))return 0;
  uint64_t info[8]={android_packet_epoch,packet.serial,packet.end_refresh,packet.page,generation,android_packet_audit_version,refresh,layer_queue[i].kind};
  memcpy(out,info,sizeof(info));return 1;
 }return 0;
}

size_t nf_android_observer_owned_packet(uint64_t epoch,unsigned serial,void*out,size_t capacity){
 if(!c||epoch!=nf_native_scene_epoch())return 0;
 const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
 uint64_t epochs[2]={android_previous_epoch,android_packet_epoch};
 for(unsigned i=0;i<2;i++){NFScenePacket packet;if(!data[i]||epochs[i]!=epoch||!nf_scene_packet_view(data[i],sizes[i],&packet)||packet.serial!=serial)continue;
  if(!out)return sizes[i];if(capacity<sizes[i])return 0;memcpy(out,data[i],sizes[i]);return sizes[i];
 }return 0;
}
int nf_android_observer_split(unsigned refresh,uint64_t out[12]){
 if(!c||!android_layers||!out||!android_previous||!android_packet||!android_previous_version||android_previous_version!=android_packet_audit_version||android_packet_audit_version!=nf_page_write_audit_version()||android_previous_epoch!=android_packet_epoch||android_packet_epoch!=nf_native_scene_epoch())return 0;
 NFScenePacket older,newer;
 if(!nf_scene_packet_view(android_previous,android_previous_bytes,&older)||!nf_scene_packet_view(android_packet,android_packet_bytes,&newer)||older.page==newer.page||older.end_refresh>=newer.end_refresh||refresh!=newer.end_refresh)return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==android_packet_epoch&&layer_queue[i].refresh==refresh){
  if(!layer_queue[i].kind)return 0;unsigned cut=0;
  for(unsigned y=0;y<160;y++){
   unsigned display=layer_queue[i].display_control[y],page=(display>>4)&1;
   if((display&7)!=4||(display&0x8080)||layer_queue[i].generation_version[y]!=android_packet_audit_version)return 0;
   if(page==newer.page){if(!cut){if(!y)return 0;cut=y;}if(layer_queue[i].generation[y][page]!=android_packet_generation)return 0;}
   else if(cut||page!=older.page||layer_queue[i].generation[y][page]!=android_previous_generation)return 0;
  }
  if(!cut)return 0;
  uint64_t info[12]={android_packet_epoch,older.serial,newer.serial,older.end_refresh,newer.end_refresh,older.page,newer.page,android_previous_generation,android_packet_generation,android_packet_audit_version,refresh,cut};
  memcpy(out,info,sizeof(info));return 1;
 }return 0;
}

/* Test both retained owners independently. Exactly one complete page owner
   must match; publication time alone never selects an owner. */
int nf_android_observer_display_owner(unsigned refresh,uint64_t out[8]){
 if(!c||!android_layers||!out)return 0;
 const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
 uint64_t epochs[2]={android_previous_epoch,android_packet_epoch},generations[2]={android_previous_generation,android_packet_generation},versions[2]={android_previous_version,android_packet_audit_version};
 uint64_t candidate[8];unsigned matches=0;
 for(unsigned owner=0;owner<2;owner++){
  NFScenePacket packet;uint64_t generation;
  if(!data[owner]||epochs[owner]!=nf_native_scene_epoch()||!versions[owner]||versions[owner]!=nf_page_write_audit_version()||!nf_scene_packet_view(data[owner],sizes[owner],&packet)||refresh<packet.end_refresh)continue;
  if(!nf_layer_queue_page_generation(epochs[owner],refresh,packet.page,&generation)||generation!=generations[owner])continue;
  for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epochs[owner]&&layer_queue[i].refresh==refresh){
   if(layer_queue[i].kind&&nf_layer_snapshot_display_page(layer_queue[i].snapshot,packet.page)){
    uint64_t info[8]={epochs[owner],packet.serial,packet.end_refresh,packet.page,generation,versions[owner],refresh,layer_queue[i].kind};memcpy(candidate,info,sizeof(info));matches++;
   }break;
  }
 }
 if(matches!=1)return 0;memcpy(out,candidate,sizeof(candidate));return 1;
}

/* Copied diagnostic provenance, never current-memory reconstruction. */
size_t nf_android_observer_provenance(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_layers||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){
  const size_t bytes=664*sizeof(uint64_t);if(!out)return bytes;if(capacity<bytes)return 0;
  uint64_t words[664]={epoch,refresh,layer_queue[i].mode,layer_queue[i].frontend,layer_queue[i].kind,nf_page_write_audit_version(),160,1};
  const uint8_t*data[2]={android_previous,android_packet};size_t sizes[2]={android_previous_bytes,android_packet_bytes};
  uint64_t epochs[2]={android_previous_epoch,android_packet_epoch},generations[2]={android_previous_generation,android_packet_generation},versions[2]={android_previous_version,android_packet_audit_version};
  for(unsigned owner=0;owner<2;owner++){NFScenePacket packet;if(data[owner]&&epochs[owner]==epoch&&nf_scene_packet_view(data[owner],sizes[owner],&packet)){
   uint64_t meta[8]={epochs[owner],packet.serial,packet.begin_refresh,packet.end_refresh,packet.page,generations[owner],versions[owner],1};memcpy(words+8+owner*8,meta,sizeof(meta));
  }}
  for(unsigned y=0;y<160;y++){unsigned offset=24+y*4;words[offset]=layer_queue[i].display_control[y];words[offset+1]=layer_queue[i].generation[y][0];words[offset+2]=layer_queue[i].generation[y][1];words[offset+3]=layer_queue[i].generation_version[y];}
  memcpy(out,words,bytes);return bytes;
 }return 0;
}

extern size_t nf_android_layer_pack(const NFLayerSnapshot*,void*,size_t);
/* Owner-thread atomic assembly; all four sections are caller-owned copies. */
size_t nf_android_observer_bundle(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_layers||epoch!=nf_native_scene_epoch())return 0;
 uint64_t whole[8],split[12];unsigned kind,count,cut=0,serials[2];
 if(nf_android_observer_display_owner(refresh,whole)){kind=1;count=1;serials[0]=(unsigned)whole[1];}
 else if(nf_android_observer_split(refresh,split)){kind=2;count=2;cut=(unsigned)split[11];serials[0]=(unsigned)split[1];serials[1]=(unsigned)split[2];}
 else return 0;
 const NFLayerSnapshot*layers=NULL;for(unsigned i=0;i<NF_LAYER_QUEUE_CAPACITY;i++)if(layer_queue[i].snapshot&&layer_queue[i].epoch==epoch&&layer_queue[i].refresh==refresh){layers=layer_queue[i].snapshot;break;}
 size_t sizes[4]={nf_android_observer_owned_packet(epoch,serials[0],NULL,0),count==2?nf_android_observer_owned_packet(epoch,serials[1],NULL,0):0,nf_android_layer_pack(layers,NULL,0),nf_android_observer_provenance(epoch,refresh,NULL,0)};
 if(!sizes[0]||(count==2&&!sizes[1])||!sizes[2]||sizes[3]!=5312)return 0;
 uint64_t header[16]={0x3142414e,1,128,epoch,refresh,kind,cut,count};size_t total=128;
 for(unsigned i=0;i<4;i++){if(sizes[i]>64*1024*1024-total)return 0;header[8+i*2]=total;header[9+i*2]=sizes[i];total+=sizes[i];}header[2]=total;
 if(!out)return total;if(capacity<total)return 0;
 /* Build privately so a downstream validation failure cannot partially write. */
 uint8_t*copy=malloc(total);if(!copy)return 0;memcpy(copy,header,128);int ok=1;
 for(unsigned i=0;i<count;i++)if(nf_android_observer_owned_packet(epoch,serials[i],copy+header[8+i*2],sizes[i])!=sizes[i])ok=0;
 if(nf_android_layer_pack(layers,copy+header[12],sizes[2])!=sizes[2]||nf_android_observer_provenance(epoch,refresh,copy+header[14],sizes[3])!=sizes[3])ok=0;
 if(ok)memcpy(out,copy,total);free(copy);return ok?total:0;
}

/* Source-regenerated exact endpoints, independent of original raster packets.
   Enable only on the core owner thread; immutable ROM assets copied once. */
int nf_android_observer_source_world_enable(int enabled){
 if(!c)return 0;if(!enabled){if(android_source_world)nf_live_source_world_capture_disable();android_source_world=0;return 1;}
 if(android_source_world)return 1;
 struct GBA*gba=c->board;if(!nf_live_source_world_capture_enable(gba->memory.rom,gba->memory.romSize,64u*1024u*1024u))return 0;
 android_source_world=1;return 1;
}
size_t nf_android_observer_source_world(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!c||!android_source_world||epoch!=nf_native_scene_epoch()||begin>end)return 0;
 void*packet=NULL;size_t bytes=0;unsigned stage;
 if(!nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,&stage))return 0;
 if(out&&capacity<bytes){nf_scene_packet_free(packet);return 0;}
 if(out)memcpy(out,packet,bytes);nf_scene_packet_free(packet);return bytes;
}

/* Opt-in original wall capture: bounded source store, two immutable exact owners.
   This is one component of complete assets, not permission to publish a live frame. */
static unsigned android_wall_enabled,android_wall_failed,android_wall_owns_plan;
static unsigned android_wall_old_copy,android_wall_old_sky_only;
static uint64_t android_road_ordinal;static void*android_road_store;static void*android_write_ownership;static void*android_wall_store;static uint64_t android_wall_epoch,android_wall_ordinal;
static struct {uint64_t epoch;unsigned serial,begin,end,page;size_t bytes,road_bytes;uint8_t*data,*proof,*road;} android_wall_owners[2];
static void android_wall_clear(void){nf_road_history_destroy(android_road_store);android_road_store=NULL;android_road_ordinal=0;nf_write_ownership_destroy(android_write_ownership);android_write_ownership=NULL;nf_wall_history_destroy(android_wall_store);android_wall_store=NULL;for(unsigned i=0;i<2;i++)free(android_wall_owners[i].data);memset(android_wall_owners,0,sizeof(android_wall_owners));android_wall_epoch=android_wall_ordinal=0;android_wall_failed=0;}
static int android_wall_event(uint64_t epoch,unsigned refresh,const NFSceneEvent*event){
 if(!android_wall_enabled||android_wall_failed)return 0;if(epoch!=android_wall_epoch)android_wall_boundary(1);
 if(android_wall_failed||!android_wall_store||!android_write_ownership||!nf_write_ownership_apply(android_write_ownership,epoch,refresh,event)||(event->kind==2&&!nf_wall_history_append(android_wall_store,epoch,++android_wall_ordinal,refresh,event))){android_wall_failed=1;return 0;}
 if(event->kind==1){for(unsigned i=0;i<event->count;i++){NFSceneEvent run=*event;run.count=1;run.commands=event->commands+i*17;if(!nf_road_history_append(android_road_store,epoch,++android_road_ordinal,refresh,&run)){android_wall_failed=1;return 0;}}}return 1;
}
static void android_wall_boundary(int force){
 if(!android_wall_enabled||(!force&&android_wall_epoch==nf_native_scene_epoch()))return;
 android_wall_clear();android_wall_epoch=nf_native_scene_epoch();
 /* Loaded state/mode changes must not leave an old shadow framebuffer as seed. */
 if(!nf_native_model_plan_trace("",live_scene.reciprocals,sizeof(live_scene.reciprocals))||!nf_native_original_wall_spans(1)){android_wall_failed=1;return;}
 android_wall_store=nf_wall_history_create(android_wall_epoch,8u*1024u*1024u);android_write_ownership=nf_write_ownership_create(android_wall_epoch);android_road_store=nf_road_history_create(android_wall_epoch,8u*1024u*1024u);if(!android_wall_store||!android_write_ownership||!android_road_store)android_wall_failed=1;
}
int nf_android_observer_wall_history_enable(int enabled){
 if(!c)return 0;
 if(!enabled){native_source_event_sink=NULL;android_wall_enabled=0;android_wall_clear();if(android_wall_owns_plan){nf_world_trace(NULL);nf_native_model_plan_trace(NULL,NULL,0);indexed_copy_capture_enabled=android_wall_old_copy;indexed_sky_only_capture=android_wall_old_sky_only;}android_wall_owns_plan=0;return 1;}
 if(android_wall_enabled)return !android_wall_failed&&!native_original_wall_failed;
 if(native_plan_enabled||native_background_capture_only||!live_scene.assembly)return 0;
 android_wall_old_copy=indexed_copy_capture_enabled;android_wall_old_sky_only=indexed_sky_only_capture;android_wall_enabled=android_wall_owns_plan=1;android_wall_boundary(1);
 if(android_wall_failed||!nf_world_trace("")){nf_android_observer_wall_history_enable(0);return 0;}
 indexed_sky_only_capture=0;indexed_copy_capture_enabled=1;native_source_event_sink=android_wall_event;return 1;
}
static void android_wall_close_owner(uint64_t epoch,const NFScenePacket*packet){
 if(!android_wall_enabled||android_wall_failed||epoch!=android_wall_epoch||native_original_wall_failed)return;
 size_t bytes=nf_wall_history_snapshot(android_wall_store,epoch,NULL,0);if(!bytes)return;
 size_t road_bytes=nf_road_history_snapshot(android_road_store,epoch,NULL,0);if(road_bytes>64u*1024u*1024u-bytes-192080){android_wall_failed=1;return;}
 uint8_t*copy=malloc(bytes+192080+road_bytes);if(!copy||nf_wall_history_snapshot(android_wall_store,epoch,copy,bytes)!=bytes){free(copy);android_wall_failed=1;return;}
 uint64_t proof_header[10]={0x3150524e,1,192080,epoch,packet->serial,packet->begin_refresh,packet->end_refresh,(uint64_t)packet->end_refresh+1,packet->page,38400};memcpy(copy+bytes,proof_header,80);if(nf_write_ownership_page(android_write_ownership,epoch,packet->page,copy+bytes+80,192000)!=192000){free(copy);android_wall_failed=1;return;}
 if(road_bytes&&nf_road_history_snapshot(android_road_store,epoch,copy+bytes+192080,road_bytes)!=road_bytes){free(copy);android_wall_failed=1;return;}
 free(android_wall_owners[0].data);android_wall_owners[0]=android_wall_owners[1];memset(&android_wall_owners[1],0,sizeof(android_wall_owners[1]));android_wall_owners[1].epoch=epoch;android_wall_owners[1].serial=packet->serial;android_wall_owners[1].begin=packet->begin_refresh;android_wall_owners[1].end=packet->end_refresh;android_wall_owners[1].page=packet->page;android_wall_owners[1].bytes=bytes;android_wall_owners[1].data=copy;android_wall_owners[1].proof=copy+bytes;android_wall_owners[1].road=copy+bytes+192080;android_wall_owners[1].road_bytes=road_bytes;
}
size_t nf_android_observer_wall_history(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){
 if(!c||!android_wall_enabled||android_wall_failed||native_original_wall_failed||epoch!=android_wall_epoch||epoch!=nf_native_scene_epoch())return 0;
 for(unsigned i=0;i<2;i++)if(android_wall_owners[i].data&&android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){size_t bytes=android_wall_owners[i].bytes;if(out&&capacity<bytes)return 0;if(out)memcpy(out,android_wall_owners[i].data,bytes);return bytes;}return 0;
}
int nf_android_observer_wall_stats(uint64_t out[8]){if(!c||!out)return 0;memset(out,0,64);out[0]=android_wall_enabled;out[1]=android_wall_failed||native_original_wall_failed;out[2]=android_wall_epoch;out[3]=android_wall_ordinal;if(android_wall_store){uint64_t stats[5];if(!nf_wall_history_stats(android_wall_store,stats))return 0;out[4]=stats[0];out[5]=stats[1];out[6]=stats[2];uint64_t road_stats[5]={0};nf_road_history_stats(android_road_store,road_stats);out[7]=stats[4]+road_stats[4]+android_wall_owners[0].road_bytes+android_wall_owners[1].road_bytes+nf_write_ownership_size()+android_wall_owners[0].bytes+android_wall_owners[1].bytes+(android_wall_owners[0].data?192080:0)+(android_wall_owners[1].data?192080:0);}return 1;}


size_t nf_android_observer_write_ownership(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!nf_android_observer_wall_history(epoch,serial,begin,end,NULL,0)||(out&&capacity<192080))return 0;for(unsigned i=0;i<2;i++)if(android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){if(out)memcpy(out,android_wall_owners[i].proof,192080);return 192080;}return 0;}

size_t nf_android_observer_road_history(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void*out,size_t capacity){if(!nf_android_observer_wall_history(epoch,serial,begin,end,NULL,0))return 0;for(unsigned i=0;i<2;i++)if(android_wall_owners[i].epoch==epoch&&android_wall_owners[i].serial==serial&&android_wall_owners[i].begin==begin&&android_wall_owners[i].end==end){size_t bytes=android_wall_owners[i].road_bytes;if(out&&capacity<bytes)return 0;if(out&&bytes)memcpy(out,android_wall_owners[i].road,bytes);return bytes;}return 0;}

static int android_sky_enabled;
int nf_android_observer_sky_enable(int enabled){if(!c)return 0;if(android_sky_enabled==(enabled!=0))return 1;if(!nf_live_sky_capture_enable(enabled))return 0;android_sky_enabled=enabled!=0;if(android_wall_enabled||android_source_world){indexed_copy_capture_enabled=1;indexed_sky_only_capture=0;}return 1;}
size_t nf_android_observer_sky(uint64_t epoch,unsigned serial,void*out,size_t capacity){
 if(!c||!android_sky_enabled||epoch!=nf_native_scene_epoch())return 0;size_t bytes=0;
 if(!nf_live_completed_sky_read(epoch,serial,0,NULL,0,&bytes)||bytes!=15192||(out&&capacity<bytes))return 0;
 if(!out)return bytes;uint8_t copy[15192];size_t written=0;if(!nf_live_completed_sky_read(epoch,serial,0,copy,sizeof(copy),&written)||written!=bytes||epoch!=nf_native_scene_epoch())return 0;memcpy(out,copy,bytes);return bytes;
}
/* NSB1 embeds the original NAB1 plus one verified NFSK/full ROM asset per owner. */
size_t nf_android_observer_sky_scene(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!android_sky_enabled)return 0;size_t scene_bytes=nf_android_observer_bundle(epoch,refresh,NULL,0);if(!scene_bytes)return 0;
 uint8_t*scene=malloc(scene_bytes);if(!scene)return 0;if(nf_android_observer_bundle(epoch,refresh,scene,scene_bytes)!=scene_bytes){free(scene);return 0;}
 uint64_t owner[16];memcpy(owner,scene,128);unsigned count=(unsigned)owner[7];if(count<1||count>2){free(scene);return 0;}size_t bytes=128+scene_bytes+count*30568;if(out&&capacity<bytes){free(scene);return 0;}
 uint8_t*copy=malloc(bytes);if(!copy){free(scene);return 0;}uint64_t header[16]={0x3142534e,1,bytes,epoch,refresh,owner[5],owner[6],count,128,scene_bytes};memcpy(copy+128,scene,scene_bytes);int ok=1;
 for(unsigned i=0;i<count;i++){
  NFScenePacket packet;if(!nf_scene_packet_view(scene+owner[8+i*2],(size_t)owner[9+i*2],&packet)){ok=0;break;}size_t at=128+scene_bytes+i*30568;header[10+i*2]=at;header[11+i*2]=30568;
  if(nf_android_observer_sky(epoch,packet.serial,copy+at,15192)!=15192){ok=0;break;}uint32_t sky[14];memcpy(sky,copy+at,56);uint64_t captured=(uint64_t)sky[2]|((uint64_t)sky[3]<<32);
  if(captured!=epoch||sky[4]<packet.begin_refresh||sky[4]>packet.end_refresh||sky[10]!=0x06002940+packet.page*0xa000||sky[12]||sky[8]<sky[9]||sky[8]-sky[9]>238||sky[9]<0x08000000||sky[9]>0x0a000000-15376||!native_surface_read(NULL,sky[9],copy+at+15192,15376)||memcmp(copy+at+56,copy+at+15192+sky[8]-sky[9],15136)){ok=0;break;}
 }
 if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);if(out)memcpy(out,copy,bytes);}else ok=0;free(copy);free(scene);return ok?bytes:0;
}

/* NRB1 normal initial SOURCE background. Requires normal source replay and exact
   closed owner; never samples current hardware framebuffer to fill unknown cells. */
size_t nf_android_observer_background_scene(uint64_t epoch,unsigned refresh,void*out,size_t capacity){
 if(!c||!android_wall_enabled||android_wall_failed||native_original_wall_failed||epoch!=android_wall_epoch||epoch!=nf_native_scene_epoch())return 0;
 size_t sn=nf_android_observer_sky_scene(epoch,refresh,NULL,0);if(!sn||sn>64u*1024u*1024u-128-2*76880)return 0;
 uint8_t*sky=malloc(sn);if(!sky)return 0;if(nf_android_observer_sky_scene(epoch,refresh,sky,sn)!=sn){free(sky);return 0;}
 uint64_t sh[16],nh[16];memcpy(sh,sky,128);memcpy(nh,sky+sh[8],128);unsigned count=(unsigned)sh[7];size_t bytes=128+sn+count*76880;
 if(count<1||count>2||(out&&capacity<bytes)){free(sky);return 0;}uint8_t*copy=malloc(bytes);if(!copy){free(sky);return 0;}uint64_t header[16]={0x3142524e,1,bytes,epoch,refresh,sh[5],sh[6],count,128,sn};memcpy(copy+128,sky,sn);int ok=1;
 for(unsigned i=0;i<count;i++){
  NFScenePacket p;if(!nf_scene_packet_view(sky+sh[8]+nh[8+i*2],(size_t)nh[9+i*2],&p)||!nf_android_observer_wall_history(epoch,p.serial,p.begin_refresh,p.end_refresh,NULL,0)||p.end_refresh==UINT32_MAX){ok=0;break;}
  unsigned closed=p.end_refresh+1,slot=closed%16,base=p.page*0xa000;size_t at=128+sn+i*76880;header[10+i*2]=at;header[11+i*2]=76880;
  if(!native_background_frames[slot].valid||native_background_frames[slot].refresh!=closed){ok=0;break;}
  uint64_t bg[10]={0x3147424e,1,76880,epoch,p.serial,p.begin_refresh,p.end_refresh,closed,p.page,38400};memcpy(copy+at,bg,80);unsigned any=0;
  for(unsigned cell=0;cell<38400;cell++){uint8_t mask=native_background_frames[slot].coverage[base+cell];if(mask>1){ok=0;break;}any|=mask;copy[at+80+cell]=native_background_frames[slot].vram[base+cell];copy[at+38480+cell]=mask;}
  if(!ok||!any){ok=0;break;}
  size_t sky_at=(size_t)sh[10+i*2];for(unsigned cell=10560;cell<25696;cell++)if(!copy[at+38480+cell]||copy[at+80+cell]!=sky[sky_at+56+cell-10560]){ok=0;break;}if(!ok)break;
 }
 if(ok&&epoch==nf_native_scene_epoch()){memcpy(copy,header,128);if(out)memcpy(out,copy,bytes);}else ok=0;free(copy);free(sky);return ok?bytes:0;
}
