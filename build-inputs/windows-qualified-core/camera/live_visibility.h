#include "road_bundle.h"
#include "road_asset.h"
/* Opt-in diagnostic attachment. Never replaces original rendering or timing. */
#include "visibility_snapshot.h"
#include "rigid_motion.h"
#include "ordered_dispatch.h"
#include "draw_palette.h"
#include "live_model_inputs_api.h"
#include "indexed_copy.h"
#include "ordered_bundle.h"
#include "road_polygon_clip.h"
API int nf_live_ordered_bundle_validate(const void*data,size_t size){NFOrderedBundle view;return nf_ordered_bundle_view(data,size,&view);}
typedef struct {void*asset;size_t size;uint32_t refresh,caller;uint64_t cycles;unsigned kind;uint32_t sky[7];} NFOwnedCopyEvent;
static struct {NFOwnedCopyEvent events[32];unsigned count,failed;uint64_t epoch;} pending_indexed_copies;
static struct {NFOwnedCopyEvent events[32];unsigned count,failed;uint64_t epoch;uint32_t serial,begin,end;} completed_indexed_copies[16];
static unsigned indexed_sky_only_capture;
static void indexed_copies_clear(void){
 for(unsigned i=0;i<pending_indexed_copies.count;i++)nf_indexed_copy_free(pending_indexed_copies.events[i].asset);
 memset(&pending_indexed_copies,0,sizeof(pending_indexed_copies));
 for(unsigned j=0;j<16;j++)for(unsigned i=0;i<completed_indexed_copies[j].count;i++)nf_indexed_copy_free(completed_indexed_copies[j].events[i].asset);
 memset(completed_indexed_copies,0,sizeof(completed_indexed_copies));
}
static void indexed_copy_capture(struct ARMCore*cpu,unsigned pc){
 if(!indexed_copy_capture_enabled)return;
 if(pending_indexed_copies.epoch&&pending_indexed_copies.epoch!=live_scene_epoch)indexed_copies_clear();
 pending_indexed_copies.epoch=live_scene_epoch;
 if(pending_indexed_copies.count>=32){pending_indexed_copies.failed=1;return;}
 unsigned sp=cpu->gprs[13];
 if(indexed_sky_only_capture&&!(pc==0x0806c180&&rd32(sp+24)==0x08004cb9&&cpu->gprs[9]==240&&cpu->gprs[10]==64&&cpu->gprs[3]==63&&(cpu->gprs[0]==0x06002940||cpu->gprs[0]==0x0600c940)))return;
 void*asset=NULL;size_t size=0;
 if(!nf_indexed_copy_create(native_surface_read,NULL,cpu->gprs[1],cpu->gprs[0],cpu->gprs[2],cpu->gprs[3],rd32(sp),rd32(sp+4),&asset,&size)){pending_indexed_copies.failed=1;return;}
 NFOwnedCopyEvent*event=pending_indexed_copies.events+pending_indexed_copies.count++;
 *event=(NFOwnedCopyEvent){asset,size,c->frameCounter(c),pc,mTimingGlobalTime(c->timing),1};
 if(pc==0x0806c180 && rd32(sp+24)==0x08004cb9 && cpu->gprs[9]==240 && cpu->gprs[10]==64 && cpu->gprs[3]==63 && (cpu->gprs[0]==0x06002940 || cpu->gprs[0]==0x0600c940)){
  uint32_t angle=rd32(0x03000214),width=cpu->gprs[9];int32_t center=(int16_t)rd32(0x03005abc);
  int32_t dividend=((int32_t)(((angle&0x3fffu)*width)<<2))>>14;
  int32_t offset=(dividend%(int32_t)width-center)&~1;
  event->sky[0]=1;event->sky[1]=angle;event->sky[2]=width;event->sky[3]=64;event->sky[4]=(uint32_t)center;event->sky[5]=cpu->gprs[1]-(uint32_t)offset;event->sky[6]=cpu->gprs[0];
 }
}
static void indexed_fill_capture(struct ARMCore*cpu,unsigned pc){
 if(!indexed_copy_capture_enabled||indexed_sky_only_capture||cpu->gprs[0]<0x06000000||cpu->gprs[0]>=0x06014000)return;
 if(pending_indexed_copies.epoch&&pending_indexed_copies.epoch!=live_scene_epoch)indexed_copies_clear();pending_indexed_copies.epoch=live_scene_epoch;
 if(pending_indexed_copies.count>=32){pending_indexed_copies.failed=1;return;}
 void*asset=NULL;size_t size=0;
 if(!nf_indexed_fill_create(cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],&asset,&size)){pending_indexed_copies.failed=1;return;}
 NFOwnedCopyEvent*event=pending_indexed_copies.events+pending_indexed_copies.count++;
 *event=(NFOwnedCopyEvent){asset,size,c->frameCounter(c),pc,mTimingGlobalTime(c->timing),2};
}
static void indexed_copies_publish(uint32_t serial,uint32_t begin,uint32_t end){
 unsigned slot=serial%16;for(unsigned i=0;i<completed_indexed_copies[slot].count;i++)nf_indexed_copy_free(completed_indexed_copies[slot].events[i].asset);
 memcpy(completed_indexed_copies[slot].events,pending_indexed_copies.events,sizeof(pending_indexed_copies.events));
 completed_indexed_copies[slot].count=pending_indexed_copies.count;completed_indexed_copies[slot].failed=pending_indexed_copies.failed;
 completed_indexed_copies[slot].epoch=live_scene_epoch;completed_indexed_copies[slot].serial=serial;completed_indexed_copies[slot].begin=begin;completed_indexed_copies[slot].end=end;
 memset(&pending_indexed_copies,0,sizeof(pending_indexed_copies));
}
/* Tie observer records to the original flip, including a rejected geometry
   assembly, so later accepted scenes never inherit another scene's sky copy. */
static void indexed_copies_scene_flip(uint32_t serial,uint32_t begin,uint32_t end,int started){
 if(started&&pending_indexed_copies.epoch==live_scene_epoch){indexed_copies_publish(serial,begin,end);return;}
 for(unsigned i=0;i<pending_indexed_copies.count;i++)nf_indexed_copy_free(pending_indexed_copies.events[i].asset);
 memset(&pending_indexed_copies,0,sizeof(pending_indexed_copies));
}
/* Sky-only observer mode: call after the scene sink is installed. No emulator
   memory writes; does not enable the heavier visibility-graph collector. */
API int nf_live_sky_capture_enable(int enabled){
 if(enabled&&(!c||!live_scene.assembly))return 0;
 indexed_copies_clear();indexed_sky_only_capture=enabled!=0;indexed_copy_capture_enabled=enabled!=0;
 if(enabled)nfsThumbTrace=thumbTrace;return 1;
}
/* Clone owned event; callers can retain across history eviction/reset. */
API int nf_live_completed_indexed_copy(uint64_t epoch,uint32_t serial,unsigned ordinal,void**out,size_t*size,uint32_t meta[3],uint64_t*cycles){
 unsigned slot=serial%16;if(!out||!size||!meta||!cycles||epoch!=live_scene_epoch||completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].failed||ordinal>=completed_indexed_copies[slot].count)return 0;
 unsigned found=0,total=0;NFOwnedCopyEvent*event=NULL;for(unsigned i=0;i<completed_indexed_copies[slot].count;i++)if(completed_indexed_copies[slot].events[i].kind==1){if(found++==ordinal)event=completed_indexed_copies[slot].events+i;total++;}if(!event)return 0;
 void*copy=malloc(event->size);if(!copy)return 0;memcpy(copy,event->asset,event->size);
 *out=copy;*size=event->size;meta[0]=event->refresh;meta[1]=event->caller;meta[2]=total;*cycles=event->cycles;return 1;
}
API int nf_live_completed_indexed_operation(uint64_t epoch,uint32_t serial,unsigned ordinal,void**out,size_t*size,uint32_t meta[4],uint64_t*cycles){
 unsigned slot=serial%16;if(!out||!size||!meta||!cycles||epoch!=live_scene_epoch||completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].failed||ordinal>=completed_indexed_copies[slot].count)return 0;
 NFOwnedCopyEvent*event=completed_indexed_copies[slot].events+ordinal;void*copy=malloc(event->size);if(!copy)return 0;memcpy(copy,event->asset,event->size);
 *out=copy;*size=event->size;meta[0]=event->refresh;meta[1]=event->caller;meta[2]=completed_indexed_copies[slot].count;meta[3]=event->kind;*cycles=event->cycles;return 1;
}
static void live_model_inputs_reset(void);
static struct {NFDrawPalettes*pending;struct {NFDrawPalettes*bank;uint64_t epoch;uint32_t serial,begin,end;} entries[16];unsigned count;uint32_t stats[4];} live_palettes;
static struct {
 NFVisibilityAssets*assets;NFVisibilityHistory*history;NFVisibilitySnapshot*pending;
 unsigned stage,prepared,state,serial,query_frame,builder_frame,selected,recovery;uint64_t epoch;
 uint32_t reciprocal[32768],base[2],query[12],view[12],stats[4],palette_stats[4],palette_detail[6];unsigned palette_valid,palette_versions;uint8_t ram[0x48000],palette[512],draw_palettes[64][512];
} live_visibility;
static NFVisibilitySnapshot*render_snapshot_pending;
static uint32_t scene_object_visits[1+2048*3];
static uint32_t snapshot_root_coherence[5];
API void nf_live_snapshot_root_coherence(uint32_t out[5]){if(out)memcpy(out,snapshot_root_coherence,20);}
static uint32_t snapshot_object_coherence[5];
API void nf_live_snapshot_object_coherence(uint32_t out[5]){if(out)memcpy(out,snapshot_object_coherence,20);}
static struct {unsigned enabled;uint32_t stats[6],retained_stats[4],ranges[32][3],count;} live_surface_audit;
API void nf_live_surface_audit_enable(int enabled){memset(&live_surface_audit,0,sizeof(live_surface_audit));live_surface_audit.enabled=enabled!=0;}
API void nf_live_surface_audit_stats(uint32_t out[6],uint32_t ranges[96]){if(out)memcpy(out,live_surface_audit.stats,24);if(ranges)memcpy(ranges,live_surface_audit.ranges,sizeof(live_surface_audit.ranges));}
API void nf_live_retained_surface_stats(uint32_t out[4]){if(out)memcpy(out,live_surface_audit.retained_stats,16);}
/* Latest billboard only, diagnostic ownership; not a scene-complete draw list. */
static struct {void*data;size_t size;uint64_t epoch;uint32_t serial,frame,object,stats[3];} live_billboard;
static void live_billboard_clear(void){nf_surface_free(live_billboard.data);live_billboard.data=NULL;live_billboard.size=0;}
API void nf_live_billboard_stats(uint32_t out[3]){if(out)memcpy(out,live_billboard.stats,12);}
API int nf_live_billboard_copy(uint64_t epoch,uint32_t serial,void**out,size_t*size){
 if(!out||!size||!live_billboard.data||epoch!=live_scene_epoch||epoch!=live_billboard.epoch||serial!=live_billboard.serial)return 0;
 void*copy=malloc(live_billboard.size);if(!copy)return 0;memcpy(copy,live_billboard.data,live_billboard.size);*out=copy;*size=live_billboard.size;return 1;
}
/* Research injection seam uses the same capture/ownership path as the CPU hook.
   A fixture reader is not evidence that gameplay reached this branch. */
API int nf_live_billboard_capture_reader(NFReadMemory read,void*user,uint32_t context,uint32_t state,uint32_t object){
 if(!live_surface_audit.enabled||!live_scene.started)return 0;
 live_billboard_clear();live_billboard.stats[0]++;
 void*data=NULL;size_t size=0;
 if(!nf_extract_billboard(read,user,context,state,&data,&size)){live_billboard.stats[2]++;return 0;}
 live_billboard.data=data;live_billboard.size=size;live_billboard.epoch=live_scene_epoch;live_billboard.serial=live_scene.serial;live_billboard.frame=c->frameCounter(c);live_billboard.object=object;live_billboard.stats[1]++;return 1;
}
API int nf_live_billboard_identity(uint64_t*epoch,uint32_t out[3]){
 if(!epoch||!out||!live_billboard.data)return 0;
 *epoch=live_billboard.epoch;out[0]=live_billboard.serial;out[1]=live_billboard.frame;out[2]=live_billboard.object;return 1;
}
static void live_billboard_event(struct ARMCore*cpu,unsigned pc){
 if(pc==0x03002578)nf_live_billboard_capture_reader(native_surface_read,NULL,cpu->gprs[0],cpu->gprs[1],cpu->gprs[7]);
}
typedef struct {NFVisibilitySnapshot*snapshot;uint32_t state_address,material_address;uint8_t state[256],material[48],palette[512];} NFRetainedSurfaceAudit;
typedef struct {NFRetainedSurfaceAudit inputs;uint32_t wall,args[6],origin[12],object_address,wall_pass[3];uint8_t region_object[164];size_t bytes,light_bytes;uint64_t hash,light_hash;} NFDeferredSurfaceAudit;
static struct {NFDeferredSurfaceAudit draws[256];unsigned count,model_slot,model_count;uint32_t stats[4];} deferred_surface_audit;
typedef struct {unsigned index,selector,count,function;NFVisibilityObjectDelta changes[256];uint8_t bits[32],before_bits[32];uint32_t matrix[12],before_matrix[12],head,maximum,before_head,before_maximum;} NFObjectReplayCallback;
#define NF_SCENE_CALLBACK_CAPACITY 128
static struct {NFObjectReplayCallback records[NF_SCENE_CALLBACK_CAPACITY];unsigned count,failed;} scene_callback_journal;
typedef struct {uint32_t address,state_address,record_address;uint8_t state[256],object[164],record[16];} NFObjectInvocation;
static struct {NFObjectInvocation items[64];uint32_t slots[64];uint8_t palettes[64][512];unsigned count,failed;} object_invocations;
static struct {uint32_t records[256][9],stack[64];unsigned count,depth,failed;} region_invocations;
typedef struct {NFVisibilitySnapshot*snapshot,*render_snapshot;NFVisibilityIdentity id;uint32_t visits[1+2048*3];unsigned region_count,region_failed;uint32_t regions[256][9];unsigned object_count,object_failed;NFObjectInvocation objects[64];uint32_t object_slots[64];uint8_t object_palettes[64][512];unsigned count,model_slot,model_count,page,callback_count,callback_failed;NFObjectReplayCallback callbacks[NF_SCENE_CALLBACK_CAPACITY];NFDeferredSurfaceAudit draws[256];} NFCompletedSurfaceAudit;
#define NF_COMPLETED_SURFACE_HISTORY 16
static NFCompletedSurfaceAudit*completed_surface_audit[NF_COMPLETED_SURFACE_HISTORY];
API int nf_live_completed_object_invocations(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void*out,unsigned capacity,unsigned*count){
 if(epoch!=live_scene_epoch||!out||!count)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end){
   if(e->object_failed||capacity<e->object_count)return 0;
   memcpy(out,e->objects,e->object_count*sizeof(e->objects[0]));*count=e->object_count;return 1;
  }
 }
 return 0;
}
API int nf_live_completed_object_invocation_slot(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned index,uint32_t*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&!e->object_failed&&index<e->object_count&&e->model_count==1&&e->object_slots[index]<=e->count+1){*out=e->object_slots[index];return 1;}
 }
 return 0;
}
API int nf_live_completed_object_invocation_palette(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned index,void*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&!e->object_failed&&index<e->object_count){memcpy(out,e->object_palettes[index],512);return 1;}
 }
 return 0;
}
API int nf_live_completed_region_invocations(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void*out,unsigned capacity,unsigned*count){
 if(epoch!=live_scene_epoch||!out||!count)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end){
   if(e->region_failed||capacity<e->region_count)return 0;
   memcpy(out,e->regions,e->region_count*36);*count=e->region_count;return 1;
  }
 }
 return 0;
}
static uint32_t region_origin[12],region_object_address;
static uint32_t captured_wall_pass[3]; /* entry LR, input mask, region record */
static uint8_t region_object_capture[164];
/* Diagnostic bounded copy from the owned scene snapshot, without draw overlays. */
API int nf_live_completed_snapshot_read(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t address,void*out,size_t size){
 if(epoch!=live_scene_epoch||!out||!size||size>65536)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry)return 0;
 void*copy=malloc(size);if(!copy)return 0;
 int ok=nf_visibility_snapshot_read(entry->snapshot,address,copy,size);if(ok)memcpy(out,copy,size);free(copy);return ok;
}
API int nf_live_completed_render_read(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t address,void*out,size_t size){
 if(epoch!=live_scene_epoch||!out||!size||size>65536)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry)return 0;
 void*copy=malloc(size);if(!copy)return 0;
 int ok=nf_visibility_snapshot_read(entry->render_snapshot,address,copy,size);if(ok)memcpy(out,copy,size);free(copy);return ok;
}
/* Completed-scene pose operations remain scoped to the active epoch. */
API int nf_live_completed_visibility_pose(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,NFVisibilityPoseInputs*out){
 if(epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&nf_visibility_snapshot_pose(completed_surface_audit[i]->snapshot,epoch,serial,begin,end,out))return 1;
 return 0;
}
API int nf_live_completed_visibility_at(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,NFVisibilityResult*out){
 if(epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&nf_visibility_snapshot_evaluate_at(completed_surface_audit[i]->snapshot,epoch,serial,begin,end,pose,out))return 1;
 return 0;
}
API int nf_live_completed_region_at(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned ordinal,NFVisibilityRegionResult*out){
 if(epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&nf_visibility_snapshot_region_at(completed_surface_audit[i]->snapshot,epoch,serial,begin,end,pose,ordinal,out))return 1;
 return 0;
}
/* Draw-time state bounds, not the older visibility snapshot's RAM state. */
API int nf_live_completed_surface_bounds(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint16_t out[4]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count){memcpy(out,e->draws[ordinal].inputs.state+0xe2,8);return 1;}
 }
 return 0;
}
API int nf_live_completed_surface_origin(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint32_t out[12]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count){memcpy(out,e->draws[ordinal].origin,48);return 1;}}return 0;
}
API int nf_live_completed_wall_pass(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint32_t out[3]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count&&e->draws[ordinal].wall){memcpy(out,e->draws[ordinal].wall_pass,12);return 1;}}return 0;
}
/* Owned object-selected region payload: address, object164, reconstructed record16. */
API int nf_live_completed_object_region(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,void*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count){
   NFDeferredSurfaceAudit*d=&e->draws[ordinal];uint8_t result[184]={0};
   if(!d->object_address||d->origin[6]!=0x03002364||nfs_visibility_object_region(d->inputs.state,d->region_object,result+168)!=1||memcmp(result+168,d->origin+2,16))return 0;
   memcpy(result,&d->object_address,4);memcpy(result+4,d->region_object,164);memcpy(out,result,184);return 1;
  }
 }return 0;
}
API int nf_live_completed_wall_plan(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned ordinal,NFSampledWallPlan*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&nf_visibility_snapshot_wall_plan(completed_surface_audit[i]->snapshot,epoch,serial,begin,end,pose,ordinal,out))return 1;
 return 0;
}
API int nf_live_completed_object_wall_plan(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned ordinal,NFSampledWallPlan*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count){NFDeferredSurfaceAudit*d=&e->draws[ordinal];if(!d->object_address||d->origin[6]!=0x03002364)return 0;return nf_visibility_snapshot_object_plan(e->snapshot,epoch,serial,begin,end,pose,d->inputs.state,d->region_object,out);}}
 return 0;
}
/* Invocation index includes calls which emitted no captured wall. */
API int nf_live_completed_object_invocation_plan(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned index,NFSampledWallPlan*out){
 if(epoch!=live_scene_epoch||!pose||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&!e->object_failed&&index<e->object_count){
   NFObjectInvocation*v=&e->objects[index];
   return nf_visibility_snapshot_object_plan(e->snapshot,epoch,serial,begin,end,pose,v->state,v->object,out);
  }
 }
 return 0;
}
API int nf_live_completed_queue_plans(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,NFSampledQueuePlans*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&nf_visibility_snapshot_queue_plans(completed_surface_audit[i]->snapshot,epoch,serial,begin,end,pose,out))return 1;
 return 0;
}
/* Command provenance: kind(1road,2wall,3model), draw ordinal, source,
   direct object address, region descriptor, object-selected flag. */
API int nf_live_completed_dispatch(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t*out,unsigned capacity,unsigned*out_count){
 if(epoch!=live_scene_epoch||!out||!out_count)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end){
   if(e->model_count!=1||e->model_slot>e->count||e->count>256||capacity<e->count+1)return 0;
   uint32_t result[257][6]={{0}};unsigned n=0;
   for(unsigned j=0;j<=e->count;j++){
    if(j==e->model_slot){result[n][0]=3;result[n++][1]=UINT32_MAX;}
    if(j<e->count){NFDeferredSurfaceAudit*d=&e->draws[j];result[n][0]=d->wall?2:1;result[n][1]=j;result[n][2]=d->wall?d->args[2]:d->args[1];result[n][4]=d->args[1];if(d->wall&&d->object_address&&d->origin[6]==0x03002364){result[n][3]=d->object_address;result[n][5]=1;}n++;}
   }
   memcpy(out,result,n*24);*out_count=n;return 1;
  }
 }return 0;
}
/* Selections use command indices within this exact completed scene. */
API int nf_live_completed_ordered_dispatch(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFDispatchSelection*selection,unsigned count,NFOrderedDispatch*out){
 if(!out||count>256||(!selection&&count))return 0;
 NFDispatchCommand commands[257];uint32_t passes[257][3]={{0}};unsigned n=0;
 if(!nf_live_completed_dispatch(epoch,serial,begin,end,(uint32_t*)commands,257,&n))return 0;
 for(unsigned i=0;i<n;i++)if(commands[i].kind==2&&!nf_live_completed_wall_pass(epoch,serial,begin,end,commands[i].ordinal,passes[i]))return 0;
 return nf_ordered_dispatch(commands,n,&passes[0][0],selection,count,out);
}
/* Exact retained pose only. Object groups with multiple walls are unsupported.
   This is ordering/coverage, not a geometry packet or sampled correspondence. */
API int nf_live_completed_reconstructed_order(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,NFOrderedDispatch*out){
 if(!out||epoch!=live_scene_epoch)return 0;
 NFCompletedSurfaceAudit*e=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)e=completed_surface_audit[i];
 if(!e)return 0;
 NFVisibilityPoseInputs pose;NFDispatchCommand commands[257];unsigned n=0;
 if(!nf_visibility_snapshot_pose(e->snapshot,epoch,serial,begin,end,&pose)||!nf_live_completed_dispatch(epoch,serial,begin,end,(uint32_t*)commands,257,&n))return 0;
 NFSampledQueuePlans*batch=malloc(sizeof(*batch));if(!batch)return 0;
 int ok=0;uint8_t used[NF_VISIBILITY_QUEUE_CAPACITY][64]={{0}};NFDispatchSelection selected[256];unsigned count=0;
 if(!nf_visibility_snapshot_queue_plans(e->snapshot,epoch,serial,begin,end,&pose,batch)||batch->count>NF_VISIBILITY_QUEUE_CAPACITY)goto done;
 for(unsigned i=0;i<n;i++)if(commands[i].kind==2){
  NFDeferredSurfaceAudit*d=&e->draws[commands[i].ordinal];unsigned pass=d->wall_pass[1]!=0;NFSampledWallDraw*match=NULL;
  NFSampledWallPlan object_plan;
  if(commands[i].object_selected){
   /* Reject repeated groups until explicit invocation IDs are available. */
   for(unsigned j=0;j<i;j++)if(commands[j].kind==2&&commands[j].object_selected&&commands[j].object==commands[i].object&&commands[j].descriptor==commands[i].descriptor&&!memcmp(e->draws[commands[j].ordinal].origin+2,d->origin+2,16))goto done;
   if(!nf_visibility_snapshot_object_plan(e->snapshot,epoch,serial,begin,end,&pose,d->inputs.state,d->region_object,&object_plan)||object_plan.count!=1||memcmp(object_plan.record,d->origin+2,16))goto done;
   match=&object_plan.draws[0];
  }else{
   unsigned qi_match=0,di_match=0;
   for(unsigned q=0;q<batch->count;q++){
    NFSampledWallPlan*p=&batch->plans[q];if(p->count>64)goto done;
    if(memcmp(p->record,d->origin+2,16))continue;
    for(unsigned k=0;k<p->count;k++)if(!used[q][k]&&p->draws[k].source==commands[i].source&&p->draws[k].pass==pass){if(match)goto done;match=&p->draws[k];qi_match=q;di_match=k;}
   }
   if(!match)goto done;
   used[qi_match][di_match]=1;
  }
  if(match->source!=commands[i].source||match->pass!=pass||match->draw.resolved_material!=d->args[4]||match->draw.flags!=d->args[5])goto done;
  selected[count++]=(NFDispatchSelection){i,match->source,match->pass,commands[i].object_selected};
 }
 for(unsigned q=0;q<batch->count;q++)for(unsigned k=0;k<batch->plans[q].count;k++)if(!used[q][k])goto done;
 ok=nf_live_completed_ordered_dispatch(epoch,serial,begin,end,selected,count,out);
done:free(batch);return ok;
}
/* Sample queue-wall bounds by unique source/pass. Repeated sampled sources
   reject; new entrants are counted, not silently inserted into captured order.
   Output is per captured draw ordinal: four u16 bounds, zero means hidden. */
API int nf_live_completed_sampled_bounds(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,uint16_t*out,unsigned capacity,unsigned*entrants){
 if(!pose||!out||!entrants||epoch!=live_scene_epoch)return 0;
 NFCompletedSurfaceAudit*e=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)e=completed_surface_audit[i];
 if(!e||e->count>256||capacity<e->count)return 0;
 NFSampledQueuePlans*batch=malloc(sizeof(*batch));if(!batch)return 0;
 uint16_t result[256][4]={{0}};uint8_t used[NF_VISIBILITY_QUEUE_CAPACITY][64]={{0}};unsigned extra=0;int ok=0;
 if(!nf_visibility_snapshot_queue_plans(e->snapshot,epoch,serial,begin,end,pose,batch)||batch->count>NF_VISIBILITY_QUEUE_CAPACITY)goto done;
 for(unsigned i=0;i<e->count;i++){
  NFDeferredSurfaceAudit*d=&e->draws[i];
  if(!d->wall){memcpy(result[i],d->inputs.state+0xe2,8);continue;}
  if(d->object_address&&d->origin[6]==0x03002364){
   NFSampledWallPlan object;
   if(!nf_visibility_snapshot_object_plan(e->snapshot,epoch,serial,begin,end,pose,d->inputs.state,d->region_object,&object)||object.count>1)goto done;
   if(object.count){if(object.draws[0].source!=d->args[2]||object.draws[0].pass!=(d->wall_pass[1]!=0))goto done;memcpy(result[i],object.record+2,8);}
   continue;
  }
  unsigned matches=0,mq=0,mk=0;
  for(unsigned q=0;q<batch->count;q++){
   if(batch->plans[q].count>64)goto done;
   for(unsigned k=0;k<batch->plans[q].count;k++)if(batch->plans[q].draws[k].source==d->args[2]&&batch->plans[q].draws[k].pass==(d->wall_pass[1]!=0)){matches++;mq=q;mk=k;}
  }
  if(matches>1)goto done;
  if(matches){if(used[mq][mk])goto done;used[mq][mk]=1;memcpy(result[i],batch->plans[mq].record+2,8);}
 }
 for(unsigned q=0;q<batch->count;q++)for(unsigned k=0;k<batch->plans[q].count;k++)extra+=!used[q][k];
 memcpy(out,result,e->count*8);*entrants=extra;ok=1;
done:free(batch);return ok;
}
/* Produce owned render transport with reconstructed ordering. Input packet
   remains borrowed for this call only. Release via nf_scene_packet_free. */
API int nf_live_completed_ordered_packet(uint64_t epoch,const void*data,size_t size,void**out,size_t*out_size){
 if(!data||!out||!out_size)return 0;
 NFScenePacket packet;NFOrderedDispatch order;NFDispatchCommand commands[257];unsigned count=0;
 if(!nf_scene_packet_view(data,size,&packet)||
    !nf_live_completed_reconstructed_order(epoch,packet.serial,packet.begin_refresh,packet.end_refresh,&order)||
    !nf_live_completed_dispatch(epoch,packet.serial,packet.begin_refresh,packet.end_refresh,(uint32_t*)commands,257,&count))return 0;
 uint32_t n;memcpy(&n,packet.section[2].data+4,4);
 if(n!=count||order.count!=count)return 0;
 uint32_t words[259];memcpy(words,packet.section[2].data,8);
 for(unsigned i=0;i<count;i++){
  uint32_t surface;memcpy(&surface,packet.section[2].data+8+i*4,4);
  if(commands[i].kind==3){if(surface!=UINT32_MAX)return 0;}
  else{
   if(surface==UINT32_MAX)return 0;
   uint32_t identity[5];memcpy(identity,packet.section[4].data+8+surface*20,20);
   if(identity[0]!=commands[i].kind||identity[2]!=commands[i].source)return 0;
  }
  if(order.indices[i]>=count)return 0;
  memcpy(words+2+i,packet.section[2].data+8+order.indices[i]*4,4);
 }
 packet.section[2]=(NFSceneSection){(const uint8_t*)words,8+count*4};
 return nf_scene_packet_build(&packet,out,out_size);
}
/* Single-owner sink adapter. Store copies bytes before temporary packet frees. */
API int nf_live_completed_publish_ordered(NFSnapshotStore*store,uint64_t epoch,const void*data,size_t size){
 if(!store)return 0;
 void*owned=NULL;size_t bytes=0;
 if(!nf_live_completed_ordered_packet(epoch,data,size,&owned,&bytes))return 0;
 int ok=nf_scene_packet_push(store,epoch,owned,bytes);
 nf_scene_packet_free(owned);return ok;
}
static void completed_surface_audit_clear(void){for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]){nf_visibility_snapshot_destroy(completed_surface_audit[i]->render_snapshot);nf_visibility_snapshot_destroy(completed_surface_audit[i]->snapshot);free(completed_surface_audit[i]);completed_surface_audit[i]=NULL;}}
API void nf_live_deferred_surface_stats(uint32_t out[4]){if(out)memcpy(out,deferred_surface_audit.stats,16);}
static uint64_t surface_audit_hash(const void*data,size_t size){const uint8_t*p=data;uint64_t h=14695981039346656037ull;for(size_t i=0;i<size;i++){h^=p[i];h*=1099511628211ull;}return h;}
static int retained_surface_audit_read_prior(void*context,uint32_t address,void*out,size_t size,int prior_available){
 NFRetainedSurfaceAudit*c=context;uint64_t end=(uint64_t)address+size;if(end>0x100000000ull)return 0;
 uint32_t bases[3]={c->state_address,c->material_address,0x05000000};size_t sizes[3]={256,48,512};const uint8_t*data[3]={c->state,c->material,c->palette};
 for(unsigned i=0;i<3;i++)if(address>=bases[i]&&end<=(uint64_t)bases[i]+sizes[i]){memcpy(out,data[i]+(address-bases[i]),size);return 1;}
 if(prior_available<0){if(!nf_visibility_snapshot_read(c->snapshot,address,out,size))return 0;}
 else if(!prior_available)return 0;
 for(unsigned i=0;i<3;i++){
  uint64_t lo=address>bases[i]?address:bases[i],hi=end<(uint64_t)bases[i]+sizes[i]?end:(uint64_t)bases[i]+sizes[i];
  if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),data[i]+(size_t)(lo-bases[i]),(size_t)(hi-lo));
 }
 return 1;
}
static int retained_surface_audit_read(void*context,uint32_t address,void*out,size_t size){return retained_surface_audit_read_prior(context,address,out,size,-1);}
/* Single-threaded extraction reader; scratch never escapes or becomes scene data. */
static uint8_t*surface_audit_scratch;static size_t surface_audit_scratch_capacity;
static uint64_t surface_audit_scratch_stats[3];
API void nf_live_surface_scratch_stats(uint64_t out[3]){if(out)memcpy(out,surface_audit_scratch_stats,sizeof(surface_audit_scratch_stats));}
static int live_surface_audit_read_prior(void*context,uint32_t address,void*out,size_t size,int*prior_available){
 if(prior_available)*prior_available=0;
 (void)context;if(!native_surface_read(NULL,address,out,size))return 0;
 live_surface_audit.stats[0]++;
 surface_audit_scratch_stats[0]++;
 size_t needed=size?size:1;
 if(needed>surface_audit_scratch_capacity){uint8_t*grown=realloc(surface_audit_scratch,needed);if(!grown){live_surface_audit.stats[5]++;return 1;}surface_audit_scratch=grown;surface_audit_scratch_capacity=needed;surface_audit_scratch_stats[1]++;surface_audit_scratch_stats[2]=needed;}
 uint8_t*prior=surface_audit_scratch;
 int available=nf_visibility_snapshot_read(live_visibility.pending,address,prior,size);
 if(prior_available)*prior_available=available;
 int equal=available&&!memcmp(prior,out,size);
 if(!available)live_surface_audit.stats[3]++;
 else if(equal)live_surface_audit.stats[1]++;
 else live_surface_audit.stats[2]++;
 if(!equal){
  unsigned i=0;for(;i<live_surface_audit.count;i++)if(live_surface_audit.ranges[i][0]==address&&live_surface_audit.ranges[i][1]==size)break;
  if(i<32){if(i==live_surface_audit.count){live_surface_audit.ranges[i][0]=address;live_surface_audit.ranges[i][1]=(uint32_t)size;live_surface_audit.count++;}live_surface_audit.ranges[i][2]++;}
 }
 return 1;
}
static int live_surface_audit_read(void*context,uint32_t address,void*out,size_t size){return live_surface_audit_read_prior(context,address,out,size,NULL);}
static uint64_t surface_read_reuse_stats[3];
API void nf_live_surface_read_reuse_stats(uint64_t out[3]){if(out)memcpy(out,surface_read_reuse_stats,sizeof(surface_read_reuse_stats));}
typedef struct {NFRetainedSurfaceAudit*retained;int exact,reuse,verify;} NFValidatedSurfaceRead;
static uint64_t surface_validation_stats[2];
static uint64_t surface_capture_profile_ticks[4];
static uint64_t surface_capture_profile_bytes[3];
API int nf_live_surface_capture_bytes_read(uint64_t out[3]){if(!out||!capture_profile_enabled)return 0;memcpy(out,surface_capture_profile_bytes,sizeof(surface_capture_profile_bytes));return 1;}
API int nf_live_surface_capture_profile_read(uint64_t out[4]){if(!out||!capture_profile_enabled||!capture_profile_frequency.QuadPart)return 0;for(unsigned i=0;i<3;i++)out[i]=(uint64_t)((double)surface_capture_profile_ticks[i]*1e9/capture_profile_frequency.QuadPart);out[3]=surface_capture_profile_ticks[3];return 1;}
static uint64_t model_validation_stats[2];static unsigned model_validation_force_full;
API void nf_live_model_validation_stats(uint64_t out[2]){if(out)memcpy(out,model_validation_stats,sizeof(model_validation_stats));}
API void nf_live_model_validation_force_full(unsigned enabled){model_validation_force_full=enabled!=0;}
static unsigned surface_validation_force_full;
API void nf_live_surface_validation_force_full(unsigned enabled){surface_validation_force_full=enabled!=0;}
API void nf_live_surface_validation_stats(uint64_t out[2]){if(out)memcpy(out,surface_validation_stats,sizeof(surface_validation_stats));}
static int validated_surface_audit_read(void*context,uint32_t address,void*out,size_t size){
 NFValidatedSurfaceRead*v=context;
 int prior_available=0;
 if(!live_surface_audit_read_prior(NULL,address,out,size,&prior_available)){v->exact=0;return 0;}
 /* Audit scratch is no longer in use after the live reader returns. */
 int matches;
 if(v->reuse&&v->retained->snapshot==live_visibility.pending&&size<=surface_audit_scratch_capacity){
  int available=retained_surface_audit_read_prior(v->retained,address,surface_audit_scratch,size,prior_available);
  matches=available&&!memcmp(out,surface_audit_scratch,size);surface_read_reuse_stats[0]++;
  if(v->verify){
   void*reference=malloc(size?size:1);if(!reference){v->exact=0;return 0;}
   int reference_available=retained_surface_audit_read(v->retained,address,reference,size);
   surface_read_reuse_stats[1]++;
   int different=available!=reference_available||(available&&memcmp(reference,surface_audit_scratch,size));free(reference);
   if(different){surface_read_reuse_stats[2]++;v->exact=0;return 0;}
  }
 }else matches=nf_memory_read_matches(retained_surface_audit_read,v->retained,address,out,size,surface_audit_scratch,surface_audit_scratch_capacity);
 if(!matches)v->exact=0;
 return 1;
}
/* Successful outputs are caller-owned and released with nf_surface_free.
   No borrowed history pointers escape; failure preserves all output slots. */
/* Regenerate grouped surface indices plus model marker from retained draw events. */
API int nf_live_completed_draw_order(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t*out,unsigned capacity,unsigned*count){
 if(epoch!=live_scene_epoch||!out||!count)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||entry->model_count!=1||entry->model_slot>entry->count||capacity<entry->count+1)return 0;
 unsigned roads=0,road=0,wall=0,n=0;uint32_t result[257];
 for(unsigned i=0;i<entry->count;i++)if(!entry->draws[i].wall)roads++;
 for(unsigned i=0;i<=entry->count;i++){
  if(i==entry->model_slot)result[n++]=UINT32_MAX;
  if(i<entry->count)result[n++]=entry->draws[i].wall?roads+wall++:road++;
 }
 memcpy(out,result,n*4);*count=n;return 1;
}
API int nf_live_completed_surface_identity(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint32_t out[5]){
 if(epoch!=live_scene_epoch||!out)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||ordinal>=entry->count)return 0;
 NFDeferredSurfaceAudit*d=&entry->draws[ordinal];uint16_t base=8;
 if(d->wall){if(d->args[2]>UINT32_MAX-44||!retained_surface_audit_read(&d->inputs,d->args[2]+44,&base,2))return 0;}
 uint32_t result[5]={d->wall?2:1,d->args[0],d->wall?d->args[2]:d->args[1],base,0};memcpy(out,result,20);return 1;
}
/* Diagnostic provenance from owned inputs only: pointer,width,height,index hash,palette hash. */
API int nf_live_completed_wall_animation(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint32_t out[12]){
 if(epoch!=live_scene_epoch||!out)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||ordinal>=entry->count||!entry->draws[ordinal].wall)return 0;
 NFDeferredSurfaceAudit*d=&entry->draws[ordinal];NFRetainedSurfaceAudit*c=&d->inputs;
 uint16_t base,anim,frame;uint32_t materials,animations,textures,offset,actual;uint8_t material[32],animation[8];
 if(d->args[2]>UINT32_MAX-44||!retained_surface_audit_read(c,d->args[2]+44,&base,2))return 0;
 memcpy(&materials,c->state+32,4);memcpy(&animations,c->state+72,4);memcpy(&textures,c->state,4);memcpy(&actual,c->material+40,4);
 uint64_t address=(uint64_t)materials+base*32ull;
 if(address>UINT32_MAX||!retained_surface_audit_read(c,(uint32_t)address,material,32))return 0;
 memcpy(&anim,material,2);address=(uint64_t)animations+anim*8ull;
 if(address>UINT32_MAX||!retained_surface_audit_read(c,(uint32_t)address,animation,8))return 0;
 memcpy(&frame,animation+2,2);address=(uint64_t)materials+((uint32_t)base+frame)*32ull;
 if(address>UINT32_MAX||!retained_surface_audit_read(c,(uint32_t)address,material,32))return 0;
 memcpy(&offset,material+4,4);
 uint32_t result[6]={base,anim,frame,(uint32_t)address,textures+offset,actual};memcpy(out,result,sizeof(result));return 1;
}
API int nf_live_completed_surface_arguments(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint32_t out[12]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end&&ordinal<e->count){memcpy(out,e->draws[ordinal].args,24);return 1;}
 }
 return 0;
}
API int nf_live_completed_texture_provenance(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,uint64_t out[5]){
 if(epoch!=live_scene_epoch||!out)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||ordinal>=entry->count)return 0;
 NFRetainedSurfaceAudit*c=&entry->draws[ordinal].inputs;uint32_t address;uint16_t shift,height;
 memcpy(&address,c->material+40,4);memcpy(&shift,c->material+36,2);memcpy(&height,c->material+38,2);
 if(shift>10||!height||height>1024)return 0;
 size_t size=(size_t)(1u<<shift)*height;uint8_t*indices=malloc(size);if(!indices)return 0;
 if(!retained_surface_audit_read(c,address,indices,size)){free(indices);return 0;}
 uint64_t result[5]={address,1u<<shift,height,surface_audit_hash(indices,size),surface_audit_hash(c->palette,512)};
 free(indices);memcpy(out,result,sizeof(result));return 1;
}
API int nf_live_completed_surface_extract(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned ordinal,void**out,size_t*out_bytes,void**out_light,size_t*out_light_bytes){
 if(epoch!=live_scene_epoch||!out||!out_bytes||!out_light||!out_light_bytes)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||ordinal>=entry->count)return 0;
 NFDeferredSurfaceAudit*d=&entry->draws[ordinal];void*surface=NULL,*light=NULL;size_t bytes=0,light_bytes=0;int ok;
 if(d->wall)ok=nf_extract_wall(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[2],d->args[3],d->args[4],d->args[5],&surface,&bytes,&light,&light_bytes);
 else ok=nf_extract_road_layer(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[3],d->args[4],d->args[5],&surface,&bytes);
 if(!ok||bytes!=d->bytes||light_bytes!=d->light_bytes||surface_audit_hash(surface,bytes)!=d->hash||surface_audit_hash(light,light_bytes)!=d->light_hash){nf_surface_free(surface);nf_surface_free(light);return 0;}
 *out=surface;*out_bytes=bytes;*out_light=light;*out_light_bytes=light_bytes;return 1;
}
API int nf_live_completed_surface_verify(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t out[2]){
 if(epoch!=live_scene_epoch||!out)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry)return 0;
 uint32_t result[2]={entry->count,0};
 for(unsigned i=0;i<entry->count;i++){
  NFDeferredSurfaceAudit*d=&entry->draws[i];void*surface=NULL,*light=NULL;size_t bytes=0,light_bytes=0;int ok;
  if(d->wall)ok=nf_extract_wall(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[2],d->args[3],d->args[4],d->args[5],&surface,&bytes,&light,&light_bytes);
  else ok=nf_extract_road_layer(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[3],d->args[4],d->args[5],&surface,&bytes);
  if(ok&&bytes==d->bytes&&light_bytes==d->light_bytes&&surface_audit_hash(surface,bytes)==d->hash&&surface_audit_hash(light,light_bytes)==d->light_hash)result[1]++;
  nf_surface_free(surface);nf_surface_free(light);
 }
 memcpy(out,result,8);return 1;
}
static void live_visibility_reset(void){nf_visibility_snapshot_destroy(render_snapshot_pending);render_snapshot_pending=NULL;memset(scene_object_visits,0,sizeof(scene_object_visits));scene_callback_journal.count=scene_callback_journal.failed=0;memset(&region_invocations,0,sizeof(region_invocations));memset(&object_invocations,0,sizeof(object_invocations));deferred_surface_audit.count=0;deferred_surface_audit.model_count=0;nf_draw_palettes_destroy(live_palettes.pending);live_palettes.pending=NULL;nf_visibility_snapshot_destroy(live_visibility.pending);live_visibility.pending=NULL;live_visibility.stage=0;live_visibility.prepared=0;live_visibility.palette_versions=0;}
static void live_owned_model_invalidate(void);
static uint8_t lifecycle_builder_end_ram[0x48000];
API void nf_live_lifecycle_builder_end_capture(uint8_t ram[0x48000]){if(ram)memcpy(ram,lifecycle_builder_end_ram,sizeof(lifecycle_builder_end_ram));}
static uint8_t lifecycle_builder_ram[0x48000];static uint32_t lifecycle_builder_registers[16];
API void nf_live_lifecycle_builder_capture(uint8_t ram[0x48000],uint32_t registers[16]){if(ram)memcpy(ram,lifecycle_builder_ram,sizeof(lifecycle_builder_ram));if(registers)memcpy(registers,lifecycle_builder_registers,64);}
static uint32_t lifecycle_visibility_hooks[12];
static unsigned retained_strip_zero[2];
static uint64_t retained_strip_epoch;
static unsigned live_source_world_capture;
static int live_model_views_requested(void){return live_source_world_capture||getenv("NF_CAPTURE_MODEL_VIEWS")!=NULL;}
static void live_visibility_close(void){live_source_world_capture=0;nf_visibility_snapshot_owned_callbacks(0);memset(retained_strip_zero,0,sizeof(retained_strip_zero));retained_strip_epoch=0;memset(lifecycle_visibility_hooks,0,sizeof(lifecycle_visibility_hooks));memset(surface_capture_profile_ticks,0,sizeof(surface_capture_profile_ticks));memset(surface_capture_profile_bytes,0,sizeof(surface_capture_profile_bytes));model_validation_force_full=0;memset(model_validation_stats,0,sizeof(model_validation_stats));surface_validation_force_full=0;memset(surface_validation_stats,0,sizeof(surface_validation_stats));free(surface_audit_scratch);surface_audit_scratch=NULL;surface_audit_scratch_capacity=0;memset(surface_audit_scratch_stats,0,sizeof(surface_audit_scratch_stats));live_owned_model_invalidate();completed_surface_audit_clear();memset(&deferred_surface_audit,0,sizeof(deferred_surface_audit));nf_draw_palettes_destroy(live_palettes.pending);live_palettes.pending=NULL;for(unsigned i=0;i<live_palettes.count;i++)nf_draw_palettes_destroy(live_palettes.entries[i].bank);memset(&live_palettes,0,sizeof(live_palettes));live_visibility_reset();nf_visibility_history_destroy(live_visibility.history);nf_visibility_assets_release(live_visibility.assets);memset(&live_visibility,0,sizeof(live_visibility));}
API int nf_live_visibility_enable(const void*rom,size_t size,size_t budget){
 live_visibility_close();if(!c||!live_scene.assembly)return 0;
 live_visibility.assets=nf_visibility_assets_create(rom,size);if(!live_visibility.assets)return 0;
 memcpy(live_visibility.reciprocal,(const uint8_t*)rom+0x627700,sizeof(live_visibility.reciprocal));
 live_visibility.history=nf_visibility_history_create(live_visibility.assets,budget);
 if(!live_visibility.history){live_visibility_close();return 0;}
 memset(retained_strip_zero,0,sizeof(retained_strip_zero));
 if(getenv("NF_CAPTURE_RETAINED_STRIP")){retained_strip_epoch=live_scene_epoch;uint8_t strip[1920];for(unsigned page=0;page<2;page++){
  for(unsigned i=0;i<sizeof(strip);i++)strip[i]=c->busRead8(c,0x06000000+page*0xa000+16*240+i);{unsigned zero=1;for(unsigned i=0;i<sizeof(strip);i++)if(strip[i])zero=0;retained_strip_zero[page]=zero;}
 }}
 indexed_sky_only_capture=0;indexed_copy_capture_enabled=getenv("NF_CAPTURE_INDEXED_COPY")!=NULL;
 nfsArmHook=onArm;nfsThumbTrace=thumbTrace;return 1;
}
API void nf_live_visibility_stats(uint32_t out[4]){if(out)memcpy(out,live_visibility.stats,16);}
API void nf_live_visibility_palette_stats(uint32_t out[4]){if(out)memcpy(out,live_visibility.palette_stats,16);}
API void nf_live_visibility_palette_detail(uint32_t out[6]){if(out)memcpy(out,live_visibility.palette_detail,24);}
static void live_visibility_check_palette(int draw){
 uint8_t current[512];live_visibility.palette_stats[1]++;
 int read_ok=native_surface_read(NULL,0x05000000,current,512);
 if(!read_ok||memcmp(current,live_visibility.palette,512)){
  live_visibility.palette_stats[2]++;live_visibility.palette_valid=0;
 }
 if(!read_ok)return;
 if(draw){
  if(!live_visibility.palette_versions){
   live_visibility.palette_detail[0]++;
   if(memcmp(current,live_visibility.palette,512))live_visibility.palette_detail[2]++;
  }else if(memcmp(current,live_visibility.draw_palettes[0],512))live_visibility.palette_detail[1]++;
  unsigned i=0;for(;i<live_visibility.palette_versions;i++)if(!memcmp(current,live_visibility.draw_palettes[i],512))break;
  if(i==live_visibility.palette_versions){
   if(i==64)live_visibility.palette_detail[5]++;
   else {memcpy(live_visibility.draw_palettes[i],current,512);live_visibility.palette_versions++;
    if(live_visibility.palette_versions>live_visibility.palette_detail[4])live_visibility.palette_detail[4]=live_visibility.palette_versions;
   }
  }
 }else if(live_visibility.palette_versions&&memcmp(current,live_visibility.draw_palettes[0],512))live_visibility.palette_detail[3]++;
}
/* Safe after nf_frame or inside the scene sink: reads only owned snapshots. */
API int nf_live_visibility_evaluate(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,NFVisibilityResult*out){
 if(epoch!=live_scene_epoch)return 0;
 return nf_visibility_history_evaluate(live_visibility.history,epoch,serial,begin,end,out);
}
API void nf_live_palette_bank_stats(uint32_t out[4]){if(out)memcpy(out,live_palettes.stats,16);}
API int nf_live_palette_draw(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned draw,uint32_t key[3],void*palette){
 if(epoch!=live_scene_epoch||!key||!palette)return 0;
 for(unsigned i=0;i<live_palettes.count;i++)if(live_palettes.entries[i].epoch==epoch&&live_palettes.entries[i].serial==serial&&live_palettes.entries[i].begin==begin&&live_palettes.entries[i].end==end){
  uint32_t id[3];uint8_t colors[512];NFDrawPalettes*b=live_palettes.entries[i].bank;
  if(!nf_draw_palettes_key(b,draw,id)||!nf_draw_palettes_read(b,epoch,serial,draw,id[0],id[1],id[2],colors,512))return 0;
  memcpy(key,id,12);memcpy(palette,colors,512);return 1;
 }
 return 0;
}
static struct {uint8_t state[256],scratch[32*52],surface[64*24];unsigned active,ready,address,descriptor,count,scratch_address,surface_address;uint32_t stats[5];} live_region_geometry;
static int candidate_snapshot_read(void*ctx,uint32_t address,void*out,size_t size){return nf_visibility_snapshot_read((NFVisibilitySnapshot*)ctx,address,out,size);}
/* Research candidate extraction from one retained scene, not visibility selection. */
API int nf_live_completed_wall_candidate(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t state,uint32_t source,void**out,size_t*size){
 if(epoch!=live_scene_epoch||!out||!size)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||!entry->count||entry->draws[0].args[0]!=state)return 0;
 uint8_t*palettes=malloc(256*512);if(!palettes)return 0;
 unsigned count=0;uint32_t key[3];
 while(count<256&&nf_live_palette_draw(epoch,serial,begin,end,count,key,palettes+count*512))count++;
 int ok=count&&nf_extract_wall_candidate(candidate_snapshot_read,entry->snapshot,state,source,palettes,count,out,size);
 free(palettes);return ok;
}
typedef struct {NFVisibilitySnapshot*snapshot;const NFObjectInvocation*invocation;} NFInvocationReader;
static int invocation_candidate_read(void*context,uint32_t address,void*out,size_t size){
 NFInvocationReader*r=context;uint32_t base=r->invocation->state_address;
 if(address>=base&&(uint64_t)address+size<=(uint64_t)base+256){memcpy(out,r->invocation->state+(address-base),size);return 1;}
 return nf_visibility_snapshot_read(r->snapshot,address,out,size);
}
static unsigned object_candidate_stage;
API unsigned nf_live_object_candidate_stage(void){return object_candidate_stage;}
API int nf_live_completed_object_candidate(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,unsigned index,void**out,size_t*size){
 object_candidate_stage=9;
 if(epoch!=live_scene_epoch||!pose||!out||!size)return 0;
 NFCompletedSurfaceAudit*e=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*v=completed_surface_audit[i];if(v&&v->id.epoch==epoch&&v->id.serial==serial&&v->id.begin_refresh==begin&&v->id.end_refresh==end)e=v;}
 if(!e||e->object_failed||index>=e->object_count)return 0;
 NFSampledWallPlan plan;
 if(!nf_live_completed_object_invocation_plan(epoch,serial,begin,end,pose,index,&plan)||plan.count!=1)return 0;
 uint8_t*palettes=malloc(256*512);if(!palettes)return 0;
 unsigned count=0;uint32_t key[3];
 while(count<256&&nf_live_palette_draw(epoch,serial,begin,end,count,key,palettes+count*512))count++;
 NFInvocationReader reader={e->snapshot,&e->objects[index]};
 object_candidate_stage=9;
 int ok=count&&nf_extract_wall_candidate_diagnostic(invocation_candidate_read,&reader,reader.invocation->state_address,plan.draws[0].source,palettes,count,out,size,&object_candidate_stage);
 free(palettes);return ok;
}
API int nf_live_completed_road_material_plan(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t state,uint32_t descriptor,uint32_t out[5]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end)return nf_road_material_plan(candidate_snapshot_read,e->snapshot,state,descriptor,out);}
 return 0;
}
API int nf_live_completed_road_candidate(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t state,uint32_t descriptor,void**out,size_t*size){
 if(epoch!=live_scene_epoch||!out||!size)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end)entry=e;}
 if(!entry)return 0;
 uint8_t*palettes=malloc(256*512);if(!palettes)return 0;unsigned count=0;uint32_t key[3];
 while(count<256&&nf_live_palette_draw(epoch,serial,begin,end,count,key,palettes+count*512))count++;
 int ok=count&&nf_extract_road_candidate(candidate_snapshot_read,entry->snapshot,state,descriptor,palettes,count,out,size);
 free(palettes);return ok;
}
API void nf_live_region_geometry_stats(uint32_t out[5]){if(out)memcpy(out,live_region_geometry.stats,20);}
static void live_region_geometry_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03001800){
  region_origin[0]=cpu->gprs[14];region_origin[1]=rd32(cpu->gprs[13]);
  memset(region_origin+2,0,16);native_surface_read(NULL,region_origin[1],region_origin+2,16);
  live_region_geometry.stats[0]++;live_region_geometry.active=live_region_geometry.ready=0;
  unsigned state=cpu->gprs[0],count=cpu->gprs[2];uint8_t descriptor[48],vertices[32*68];
  if(count>32)goto failed;
  live_region_geometry.address=state;live_region_geometry.descriptor=cpu->gprs[3];live_region_geometry.count=count;
  live_region_geometry.scratch_address=rd32(state+0x68);live_region_geometry.surface_address=rd32(state+0x6c);
  if(!native_surface_read(NULL,state,live_region_geometry.state,256)||!native_surface_read(NULL,cpu->gprs[3],descriptor,48)||!native_surface_read(NULL,cpu->gprs[1],vertices,count*68u)||!native_surface_read(NULL,live_region_geometry.scratch_address,live_region_geometry.scratch,count*52u)||!native_surface_read(NULL,live_region_geometry.surface_address,live_region_geometry.surface,sizeof(live_region_geometry.surface)))goto failed;
  if(nfs_visibility_region_transform(live_region_geometry.state,vertices,count*68u,count,native_surface_read,NULL,live_region_geometry.scratch,count*52u)!=1||!nfs_visibility_region_geometry(live_region_geometry.state,descriptor,vertices,count,rd16(rd32(cpu->gprs[13])+10),native_surface_read,NULL,live_visibility.reciprocal,live_region_geometry.scratch,count*52u,live_region_geometry.surface,sizeof(live_region_geometry.surface)))goto failed;
  live_region_geometry.active=1;return;
 failed:live_region_geometry.stats[3]++;return;
 }
 if(pc==0x03001ff4&&live_region_geometry.active){
  uint8_t state[256],scratch[32*52],surface[64*24];live_region_geometry.active=0;
  if(!native_surface_read(NULL,live_region_geometry.address,state,256)||!native_surface_read(NULL,live_region_geometry.scratch_address,scratch,live_region_geometry.count*52u)||!native_surface_read(NULL,live_region_geometry.surface_address,surface,sizeof(surface))||memcmp(state,live_region_geometry.state,256)||memcmp(scratch,live_region_geometry.scratch,live_region_geometry.count*52u)||memcmp(surface,live_region_geometry.surface,sizeof(surface)))live_region_geometry.stats[2]++;
  else {live_region_geometry.stats[1]++;live_region_geometry.ready=1;}
 }
}
static struct {NFVisibilityWallDraw plan[32];unsigned active,count,seen,source;uint32_t mask,stats[5];} live_wall_plan;
API void nf_live_wall_plan_stats(uint32_t out[5]){if(out)memcpy(out,live_wall_plan.stats,20);}
static void live_wall_plan_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x0300264c){
  captured_wall_pass[0]=cpu->gprs[14];captured_wall_pass[1]=cpu->gprs[3];captured_wall_pass[2]=cpu->gprs[1];
  uint8_t state[256],record[16],descriptor[48],vertices[32*68],scratch[32*52];unsigned count;uint32_t state_address=cpu->gprs[0];
  live_wall_plan.stats[0]++;live_wall_plan.active=0;live_wall_plan.seen=0;
  if(!native_surface_read(NULL,state_address,state,256)||!native_surface_read(NULL,cpu->gprs[1],record,16))goto failed;
  unsigned region=record[0]|((unsigned)record[1]<<8);uint64_t da=(uint64_t)rd32(state_address+0x14)+region*48u;
  if(da>UINT32_MAX||!native_surface_read(NULL,(uint32_t)da,descriptor,48))goto failed;
  count=descriptor[2]|((unsigned)descriptor[3]<<8);if(count>32)goto failed;
  uint64_t va=(uint64_t)rd32(state_address+0x10)+(descriptor[0]|((unsigned)descriptor[1]<<8))*68u;if(va>UINT32_MAX)goto failed;
  live_wall_plan.source=(uint32_t)va;
  if(!native_surface_read(NULL,(uint32_t)va,vertices,count*68u)||!native_surface_read(NULL,rd32(state_address+0x68),scratch,count*52u)||
     !nfs_visibility_wall_draw_plan(state,vertices,count,scratch,cpu->gprs[3],native_surface_read,NULL,live_wall_plan.plan,32,&live_wall_plan.count,&live_wall_plan.mask))goto failed;
  if(live_region_geometry.ready&&live_region_geometry.address==state_address&&live_region_geometry.descriptor==(unsigned)da&&live_region_geometry.count==count&&!memcmp(scratch,live_region_geometry.scratch,count*52u)){
   /* Equal scratch bytes and unchanged state, vertices, pass and memory within
      this hook imply the same pure plan. Keep the saved-input oracle opt-in. */
   if(getenv("NF_VERIFY_WALL_PLAN_REUSE")){
    NFVisibilityWallDraw reference[32];unsigned reference_count=0;uint32_t reference_mask=0;
    if(!nfs_visibility_wall_draw_plan(state,vertices,count,live_region_geometry.scratch,cpu->gprs[3],native_surface_read,NULL,reference,32,&reference_count,&reference_mask)||reference_count!=live_wall_plan.count||reference_mask!=live_wall_plan.mask||memcmp(reference,live_wall_plan.plan,reference_count*sizeof(*reference)))goto failed;
   }
   live_region_geometry.stats[4]++;
  }
  live_wall_plan.active=1;return;
 failed:live_wall_plan.stats[4]++;return;
 }
 if(!live_wall_plan.active)return;
 if(pc==0x03000304){
  live_wall_plan.stats[1]++;unsigned i=live_wall_plan.seen++;
  if(i>=live_wall_plan.count){live_wall_plan.stats[3]++;return;}
  NFVisibilityWallDraw*p=&live_wall_plan.plan[i];unsigned material=cpu->gprs[0];
  if(live_wall_plan.source+p->edge*68!=(unsigned)cpu->gprs[6]||p->resolved_material!=(unsigned)cpu->gprs[3]||p->flags!=(unsigned)cpu->gprs[2]||p->texture!=rd32(material+40)||p->shift!=rd16(material+36)||p->height!=rd16(material+38))live_wall_plan.stats[3]++;
 }else if(pc==0x030027e4){
  if(live_wall_plan.seen!=live_wall_plan.count||live_wall_plan.mask!=(unsigned)cpu->gprs[0])live_wall_plan.stats[3]++;
  else live_wall_plan.stats[2]++;
  live_wall_plan.active=0;
 }
}
static struct {struct {uint32_t children[512];unsigned count,next,pass;} stack[64];unsigned depth;uint32_t stats[9];} live_region_links;
API void nf_live_region_link_stats(uint32_t out[9]){if(out)memcpy(out,live_region_links.stats,36);}
static uint32_t live_object_region_stats[7],live_object_changed_words[41];
API void nf_live_object_changed_words(uint32_t out[41]){if(out)memcpy(out,live_object_changed_words,sizeof(live_object_changed_words));}
API void nf_live_object_region_stats(uint32_t out[7]){if(out)memcpy(out,live_object_region_stats,28);}
static void live_region_link_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x030027f0){
  live_region_links.stats[0]++;unsigned region=rd16(cpu->gprs[1]);
  if(live_region_links.depth){
   unsigned parent=live_region_links.depth-1;
   if((unsigned)cpu->gprs[14]==0x03002364){
    live_region_links.stats[8]++;live_object_region_stats[0]++;
    uint8_t state[256],object[164]={0},original[16],native[16]={0},prior[164];
    if(!native_surface_read(NULL,cpu->gprs[0],state,256)||!native_surface_read(NULL,cpu->gprs[7],object,164)||!native_surface_read(NULL,cpu->gprs[1],original,16)||nfs_visibility_object_region(state,object,native)!=1)live_object_region_stats[2]++;
    else if(memcmp(original,native,16)||cpu->gprs[2])live_object_region_stats[2]++;
    else live_object_region_stats[1]++;
    if(live_visibility.pending&&nf_visibility_snapshot_read(live_visibility.pending,cpu->gprs[7],prior,164)){
     if(memcmp(prior,object,164))live_object_region_stats[3]++;
     for(unsigned word=0;word<41;word++)if(memcmp(prior+word*4,object+word*4,4))live_object_changed_words[word]++;
     if(memcmp(prior+10,object+10,2))live_object_region_stats[5]++;
     if(memcmp(prior+0x36,object+0x36,2))live_object_region_stats[6]++;
    }else live_object_region_stats[4]++;
   }
   else {
   if(live_region_links.stack[parent].next>=live_region_links.stack[parent].count||live_region_links.stack[parent].children[live_region_links.stack[parent].next++]!=region||live_region_links.stack[parent].pass!=(unsigned)cpu->gprs[2])live_region_links.stats[5]++;
   live_region_links.stats[1]++;
   if((unsigned)cpu->gprs[14]==0x03002918)live_region_links.stats[2]++;
   else if((unsigned)cpu->gprs[14]==0x03002ae8)live_region_links.stats[3]++;
   else live_region_links.stats[5]++;
   }
  }
  if(live_region_links.depth==64){live_region_links.stats[6]++;return;}
  unsigned slot=live_region_links.depth++;if(live_region_links.depth>live_region_links.stats[4])live_region_links.stats[4]=live_region_links.depth;
  live_region_links.stack[slot].count=live_region_links.stack[slot].next=0;live_region_links.stack[slot].pass=cpu->gprs[2];
  if(cpu->gprs[2]){live_region_links.stats[7]++;return;}
  uint8_t state[256],descriptor[48];unsigned replace;
  uint64_t address=(uint64_t)rd32(cpu->gprs[0]+0x14)+region*48u;
  if(address>UINT32_MAX||!native_surface_read(NULL,cpu->gprs[0],state,256)||!native_surface_read(NULL,(uint32_t)address,descriptor,48)||!nfs_visibility_region_links(state,descriptor,native_surface_read,NULL,live_region_links.stack[slot].children,512,&live_region_links.stack[slot].count,&replace))live_region_links.stats[6]++;
 }else if(pc==0x03002b68){if(live_region_links.depth)live_region_links.depth--;else live_region_links.stats[5]++;}
}
static struct {uint32_t expected[3],stats[5];unsigned active,object;} live_object_distance;
API void nf_live_object_distance_stats(uint32_t out[5]){if(out)memcpy(out,live_object_distance.stats,20);}
static void live_object_distance_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x0300209c){
  uint32_t matrix[12];uint8_t object[164];live_object_distance.active=0;live_object_distance.stats[0]++;live_object_distance.object=cpu->gprs[6];
  if(!native_surface_read(NULL,rd32(cpu->gprs[7]+0x54),matrix,48)||!native_surface_read(NULL,cpu->gprs[6],object,164)||!nfs_visibility_object_distance(matrix,object,live_object_distance.expected)){live_object_distance.stats[3]++;return;}
  live_object_distance.active=1;
 }else if(pc==0x030020f0&&live_object_distance.active){
  live_object_distance.active=0;
  if(live_object_distance.expected[0]!=(unsigned)cpu->gprs[2]||live_object_distance.expected[1]!=(unsigned)cpu->gprs[0]||live_object_distance.expected[2]!=(unsigned)cpu->gprs[4]||live_object_distance.expected[2]!=rd32(live_object_distance.object+0x28))live_object_distance.stats[2]++;
  else live_object_distance.stats[1]++;
  if((int32_t)live_object_distance.expected[1]<=0)live_object_distance.stats[4]++;
 }
}
static struct {uint8_t objects[512*164];unsigned active,base,count;uint32_t head,maximum,stats[5];} live_object_insert;
API void nf_live_object_insert_stats(uint32_t out[5]){if(out)memcpy(out,live_object_insert.stats,20);}
static void live_object_insert_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x030020f8){
  live_object_insert.stats[0]++;live_object_insert.active=0;
  unsigned base=rd32(cpu->gprs[7]+0x3c),address=cpu->gprs[6];
  if(address<base||(address-base)%164)goto failed;
  unsigned candidate=(address-base)/164,highest=candidate,node=rd32(0x030070e0),steps=0;uint8_t seen[512]={0},object[164];
  if(candidate>=512)goto failed;
  while(node!=65535){
   if(node>=512||seen[node]||++steps>512||(uint64_t)base+node*164u>UINT32_MAX)goto failed;
   seen[node]=1;if(node>highest)highest=node;
   if(!native_surface_read(NULL,base+node*164u,object,164))goto failed;
   node=object[4]|((unsigned)object[5]<<8);
  }
  live_object_insert.base=base;live_object_insert.count=highest+1;
  if(highest+1>live_object_insert.stats[4])live_object_insert.stats[4]=highest+1;
  live_object_insert.head=rd32(0x030070e0);live_object_insert.maximum=rd32(0x030070a4);
  if(!native_surface_read(NULL,base,live_object_insert.objects,(highest+1)*164u)||!nfs_visibility_object_insert(live_object_insert.objects,highest+1,candidate,&live_object_insert.head,&live_object_insert.maximum))goto failed;
  live_object_insert.active=1;return;
 failed:live_object_insert.stats[3]++;return;
 }
 if(live_object_insert.active&&(pc==0x030021f8||pc==0x03002204)){
  uint8_t objects[512*164];live_object_insert.active=0;
  if(!native_surface_read(NULL,live_object_insert.base,objects,live_object_insert.count*164u)||memcmp(objects,live_object_insert.objects,live_object_insert.count*164u)||live_object_insert.head!=rd32(0x030070e0)||live_object_insert.maximum!=rd32(0x030070a4))live_object_insert.stats[2]++;
  else live_object_insert.stats[1]++;
 }
}
static struct {uint8_t objects[512*164];unsigned active,base,count;uint32_t head,maximum,stats[5];} live_object_sort;
API void nf_live_object_sort_stats(uint32_t out[5]){if(out)memcpy(out,live_object_sort.stats,20);}
static void live_object_sort_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002090){
  live_object_sort.stats[0]++;live_object_sort.active=0;
  unsigned base=rd32(cpu->gprs[7]+0x3c),address=cpu->gprs[6];
  if(address<base||(address-base)%164)goto failed;
  unsigned candidate=(address-base)/164,highest=candidate,node=rd32(0x030070e0),steps=0;uint8_t seen[512]={0},object[164];
  if(candidate>=512)goto failed;
  while(node!=65535){
   if(node>=512||seen[node]||++steps>512||(uint64_t)base+node*164u>UINT32_MAX)goto failed;
   seen[node]=1;if(node>highest)highest=node;
   if(!native_surface_read(NULL,base+node*164u,object,164))goto failed;
   node=object[4]|((unsigned)object[5]<<8);
  }
  live_object_sort.base=base;live_object_sort.count=highest+1;
  if(highest+1>live_object_sort.stats[4])live_object_sort.stats[4]=highest+1;
  live_object_sort.head=rd32(0x030070e0);live_object_sort.maximum=rd32(0x030070a4);
  uint32_t matrix[12];
  if(!native_surface_read(NULL,rd32(cpu->gprs[7]+0x54),matrix,48)||!native_surface_read(NULL,base,live_object_sort.objects,(highest+1)*164u)||nfs_visibility_object_sort(live_object_sort.objects,highest+1,candidate,matrix,&live_object_sort.head,&live_object_sort.maximum)<0)goto failed;
  live_object_sort.active=1;return;
 failed:live_object_sort.stats[3]++;return;
 }
 if(live_object_sort.active&&(pc==0x030021f8||pc==0x03002204)){
  uint8_t objects[512*164];live_object_sort.active=0;
  if(!native_surface_read(NULL,live_object_sort.base,objects,live_object_sort.count*164u)||memcmp(objects,live_object_sort.objects,live_object_sort.count*164u)||live_object_sort.head!=rd32(0x030070e0)||live_object_sort.maximum!=rd32(0x030070a4))live_object_sort.stats[2]++;
  else live_object_sort.stats[1]++;
 }
}
static struct {uint8_t visited[32];uint32_t callback,stats[7];unsigned active,expected,callback_seen;} live_object_visit;
API void nf_live_object_visit_stats(uint32_t out[7]){if(out)memcpy(out,live_object_visit.stats,28);}
static void live_object_visit_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002020){
  unsigned index=cpu->gprs[1];uint8_t object[164];uint64_t address=(uint64_t)rd32(cpu->gprs[7]+0x3c)+index*164u;
  live_object_visit.stats[0]++;live_object_visit.active=0;live_object_visit.callback_seen=0;
  if(index>=256||address>UINT32_MAX||!native_surface_read(NULL,0x030070c0,live_object_visit.visited,32)||!native_surface_read(NULL,(uint32_t)address,object,164)){live_object_visit.stats[6]++;return;}
  int result=nfs_visibility_object_visit(live_object_visit.visited,32,index,object,&live_object_visit.callback);
  if(result<0){live_object_visit.stats[6]++;return;}
  live_object_visit.expected=result;live_object_visit.active=1;
 }
 if(!live_object_visit.active)return;
 if(pc==0x03002088){
  live_object_visit.callback_seen++;live_object_visit.stats[3]++;
  if(live_object_visit.callback!=(unsigned)cpu->gprs[2])live_object_visit.stats[5]++;
 }
 if(pc==0x03002090||pc==0x030021f8){
  uint8_t actual[32];unsigned result=pc==0x03002090;
  live_object_visit.active=0;live_object_visit.stats[result?1:2]++;
  if(!native_surface_read(NULL,0x030070c0,actual,32)||memcmp(actual,live_object_visit.visited,32)||result!=live_object_visit.expected||live_object_visit.callback_seen!=(live_object_visit.callback!=65535))live_object_visit.stats[5]++;
  else live_object_visit.stats[4]++;
 }
}
static struct {NFVisibilityObjectCursor cursor;unsigned active;uint32_t stats[6];} live_object_cursor;
API void nf_live_object_cursor_stats(uint32_t out[6]){if(out)memcpy(out,live_object_cursor.stats,24);}
static void live_object_cursor_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002000){
  if(live_object_cursor.active)live_object_cursor.stats[4]++;
  live_object_cursor.stats[0]++;
  int result=nfs_visibility_object_cursor_begin(&live_object_cursor.cursor,cpu->gprs[1],256);
  live_object_cursor.active=result>=0;
  if(result<0)live_object_cursor.stats[5]++;
 }
 if(!live_object_cursor.active)return;
 if(pc==0x03002020){
  live_object_cursor.stats[1]++;
  if(live_object_cursor.cursor.current!=(unsigned)cpu->gprs[1])live_object_cursor.stats[4]++;
 }
 if(pc==0x030021f8){
  uint8_t object[164];
  if(!native_surface_read(NULL,cpu->gprs[6],object,164)||nfs_visibility_object_cursor_advance(&live_object_cursor.cursor,object)<0){live_object_cursor.stats[5]++;live_object_cursor.active=0;}
  else live_object_cursor.stats[2]++;
 }
 if(pc==0x03002204){
  if(live_object_cursor.cursor.current!=65535)live_object_cursor.stats[4]++;
  else live_object_cursor.stats[3]++;
  live_object_cursor.active=0;
 }
}


/* Owned inputs/outcomes for replay; replay function performs no emulator reads. */

static struct {uint8_t objects[256*164],bits[32];uint32_t matrix[12],head,maximum,source,stats[4];unsigned count;NFObjectReplayCallback callbacks[32];} live_object_replay;
API void nf_live_object_replay_stats(uint32_t out[4]){if(out)memcpy(out,live_object_replay.stats,16);}
static int live_object_replay_verify(const uint8_t*expected,const uint8_t*bits,uint32_t head,uint32_t maximum){
 uint8_t objects[256*164],visited[32];uint32_t matrix[12],h=live_object_replay.head,m=live_object_replay.maximum,selector;unsigned used=0;
 NFVisibilityObjectCollector collector={0};
 memcpy(objects,live_object_replay.objects,sizeof(objects));memcpy(visited,live_object_replay.bits,32);memcpy(matrix,live_object_replay.matrix,48);
 if(nfs_visibility_object_cursor_begin(&collector.cursor,live_object_replay.source,256)<0)return 0;
 for(unsigned step=0;step<1025;step++){
  int result=nfs_visibility_object_collect_step(&collector,objects,visited,32,matrix,&h,&m,&selector);
  if(result==0)return used==live_object_replay.count&&!memcmp(objects,expected,sizeof(objects))&&!memcmp(visited,bits,32)&&h==head&&m==maximum;
  if(result<0)return 0;
  if(result==2){
   if(used>=live_object_replay.count)return 0;
   NFObjectReplayCallback*r=&live_object_replay.callbacks[used++];
   if(selector!=r->selector||!nfs_visibility_object_callback_apply(&collector,objects,r->index,r->selector,r->changes,r->count))return 0;
   uint32_t globals[2]={h,m},before[2]={r->before_head,r->before_maximum},after[2]={r->head,r->maximum};
   if(!nfs_visibility_callback_state(visited,matrix,globals,r->before_bits,r->bits,r->before_matrix,r->matrix,before,after))return 0;
   h=globals[0];m=globals[1];
  }
 }
 return 0;
}
/* Private whole-list mirror. Callback deltas are observed, never reexecuted. */
static uint32_t callback_functions[16][5];static unsigned callback_function_count;
API unsigned nf_live_callback_functions(uint32_t out[16][5]){if(out)memcpy(out,callback_functions,sizeof(callback_functions));return callback_function_count;}
static struct {
 NFVisibilityObjectCollector collector;
 uint8_t objects[256*164],before[256*164],visited[32],before_visited[32];
 uint32_t matrix[12],head,maximum,base,matrix_address,stats[6];
 uint32_t before_matrix[12],before_head,before_maximum,effects[7],selector,callback_function,callback_object,delta_count,delta_overflow,deltas[32][6];
 unsigned active,waiting;
} live_object_collector;
API void nf_live_object_collector_stats(uint32_t out[6]){if(out)memcpy(out,live_object_collector.stats,24);}
API void nf_live_object_callback_effects(uint32_t out[7]){if(out)memcpy(out,live_object_collector.effects,28);}
API unsigned nf_live_object_callback_deltas(uint32_t out[32][6],uint32_t*overflow){if(out)memcpy(out,live_object_collector.deltas,sizeof(live_object_collector.deltas));if(overflow)*overflow=live_object_collector.delta_overflow;return live_object_collector.delta_count;}
static void live_object_collector_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002000){
  if(live_object_collector.active)live_object_collector.stats[4]++;
  live_object_collector.active=0;live_object_collector.waiting=0;live_object_collector.stats[0]++;
  live_object_collector.base=rd32(cpu->gprs[0]+0x3c);live_object_collector.matrix_address=rd32(cpu->gprs[0]+0x54);
  memset(&live_object_collector.collector,0,sizeof(live_object_collector.collector));
  if(nfs_visibility_object_cursor_begin(&live_object_collector.collector.cursor,cpu->gprs[1],256)<0||!native_surface_read(NULL,live_object_collector.base,live_object_collector.objects,sizeof(live_object_collector.objects))||!native_surface_read(NULL,0x030070c0,live_object_collector.visited,32)||!native_surface_read(NULL,live_object_collector.matrix_address,live_object_collector.matrix,48))goto failed;
  live_object_collector.head=rd32(0x030070e0);live_object_collector.maximum=rd32(0x030070a4);live_object_collector.active=1;
  memcpy(live_object_replay.objects,live_object_collector.objects,sizeof(live_object_replay.objects));memcpy(live_object_replay.bits,live_object_collector.visited,32);memcpy(live_object_replay.matrix,live_object_collector.matrix,48);
  live_object_replay.head=live_object_collector.head;live_object_replay.maximum=live_object_collector.maximum;live_object_replay.source=cpu->gprs[1];live_object_replay.count=0;
 }
 if(!live_object_collector.active)return;
 if(pc==0x03002020){
  uint32_t callback;
  if(live_object_collector.collector.cursor.current!=(unsigned)cpu->gprs[1])goto mismatch;
  int result=nfs_visibility_object_collect_step(&live_object_collector.collector,live_object_collector.objects,live_object_collector.visited,32,live_object_collector.matrix,&live_object_collector.head,&live_object_collector.maximum,&callback);
  if(result!=1&&result!=2)goto failed;
  live_object_collector.waiting=result==2;live_object_collector.stats[1]++;
 }
 if(pc==0x03002088&&live_object_collector.waiting){
  live_object_collector.callback_function=cpu->gprs[12];live_object_collector.selector=cpu->gprs[2];live_object_collector.callback_object=cpu->gprs[6];
  if(!native_surface_read(NULL,live_object_collector.matrix_address,live_object_collector.before_matrix,48))goto failed;
  live_object_collector.before_head=rd32(0x030070e0);live_object_collector.before_maximum=rd32(0x030070a4);
  if(!native_surface_read(NULL,live_object_collector.base,live_object_collector.before,sizeof(live_object_collector.before))||!native_surface_read(NULL,0x030070c0,live_object_collector.before_visited,32))goto failed;
 }
 if(pc==0x03002090&&live_object_collector.waiting){
  uint8_t after[256*164],bits[32];uint32_t callback;
  if(live_object_collector.base!=rd32(cpu->gprs[7]+0x3c)||live_object_collector.matrix_address!=rd32(cpu->gprs[7]+0x54))goto failed;
  if(!native_surface_read(NULL,live_object_collector.base,after,sizeof(after))||!native_surface_read(NULL,0x030070c0,bits,32)||!native_surface_read(NULL,live_object_collector.matrix_address,live_object_collector.matrix,48))goto failed;
  unsigned changed=0;NFVisibilityObjectDelta changes[256];
  for(unsigned i=0;i<sizeof(after);i++)if(after[i]!=live_object_collector.before[i]){
   if(changed>=256)goto failed;
   changes[changed++]=(NFVisibilityObjectDelta){i,live_object_collector.before[i],after[i]};
   if(live_object_collector.delta_count<32){uint32_t*d=live_object_collector.deltas[live_object_collector.delta_count++];d[0]=live_object_collector.selector;d[1]=live_object_collector.callback_object;d[2]=live_object_collector.base;d[3]=i;d[4]=live_object_collector.before[i];d[5]=after[i];}else live_object_collector.delta_overflow++;}
  if(!nfs_visibility_object_callback_apply(&live_object_collector.collector,live_object_collector.objects,live_object_collector.collector.cursor.current,live_object_collector.selector,changes,changed))goto failed;
  unsigned function_slot=0;while(function_slot<callback_function_count&&(callback_functions[function_slot][0]!=live_object_collector.callback_function||callback_functions[function_slot][1]!=live_object_collector.selector))function_slot++;
  if(function_slot<16){if(function_slot==callback_function_count){callback_function_count++;callback_functions[function_slot][0]=live_object_collector.callback_function;callback_functions[function_slot][1]=live_object_collector.selector;}callback_functions[function_slot][2]++;callback_functions[function_slot][3]+=changed!=0;callback_functions[function_slot][4]+=changed;}
  live_object_collector.effects[0]++;live_object_collector.effects[1]+=changed!=0;live_object_collector.effects[2]+=changed;
  live_object_collector.effects[3]+=memcmp(bits,live_object_collector.before_visited,32)!=0;
  live_object_collector.effects[4]+=memcmp(live_object_collector.matrix,live_object_collector.before_matrix,48)!=0;
  live_object_collector.effects[5]+=rd32(0x030070e0)!=live_object_collector.before_head;
  live_object_collector.effects[6]+=rd32(0x030070a4)!=live_object_collector.before_maximum;
  for(unsigned i=0;i<32;i++)if(bits[i]!=live_object_collector.before_visited[i])live_object_collector.visited[i]=bits[i];
  /* These globals are caller-owned callback state; observed values resume it. */
  live_object_collector.head=rd32(0x030070e0);live_object_collector.maximum=rd32(0x030070a4);
  if(live_object_replay.count>=32){live_object_replay.stats[3]++;goto failed;}
  NFObjectReplayCallback*record=&live_object_replay.callbacks[live_object_replay.count++];
  record->function=live_object_collector.callback_function;record->index=live_object_collector.collector.cursor.current;record->selector=live_object_collector.selector;record->count=changed;
  memcpy(record->changes,changes,changed*sizeof(*changes));memcpy(record->bits,live_object_collector.visited,32);memcpy(record->matrix,live_object_collector.matrix,48);memcpy(record->before_matrix,live_object_collector.before_matrix,48);record->head=live_object_collector.head;record->maximum=live_object_collector.maximum;record->before_head=live_object_collector.before_head;record->before_maximum=live_object_collector.before_maximum;memcpy(record->before_bits,live_object_collector.before_visited,32);
  if(scene_callback_journal.count>=NF_SCENE_CALLBACK_CAPACITY)scene_callback_journal.failed=1;else scene_callback_journal.records[scene_callback_journal.count++]=*record;
  if(nfs_visibility_object_collect_step(&live_object_collector.collector,live_object_collector.objects,live_object_collector.visited,32,live_object_collector.matrix,&live_object_collector.head,&live_object_collector.maximum,&callback)!=1)goto failed;
  live_object_collector.waiting=0;live_object_collector.stats[2]++;
 }
 if(pc==0x030021f8||pc==0x03002204){
  uint8_t actual[256*164],bits[32];
  if(!native_surface_read(NULL,live_object_collector.base,actual,sizeof(actual))||!native_surface_read(NULL,0x030070c0,bits,32))goto failed;
  if(memcmp(actual,live_object_collector.objects,sizeof(actual))||memcmp(bits,live_object_collector.visited,32)||live_object_collector.head!=rd32(0x030070e0)||live_object_collector.maximum!=rd32(0x030070a4))goto mismatch;
  if(pc==0x03002204){
   if(live_object_collector.collector.cursor.current!=65535||live_object_collector.waiting)goto mismatch;
   live_object_replay.stats[0]++;
   if(live_object_replay_verify(live_object_collector.objects,live_object_collector.visited,live_object_collector.head,live_object_collector.maximum))live_object_replay.stats[1]++;else live_object_replay.stats[2]++;
   live_object_collector.stats[3]++;live_object_collector.active=0;
  }
 }
 return;
 mismatch:scene_callback_journal.failed=1;live_object_collector.stats[4]++;live_object_collector.active=0;return;
 failed:scene_callback_journal.failed=1;live_object_collector.stats[5]++;live_object_collector.active=0;
}

static struct {uint8_t state[256];uint32_t xyz[3],address,stats[5];unsigned active;} live_object_draw_setup;
API void nf_live_object_draw_setup_stats(uint32_t out[5]){if(out)memcpy(out,live_object_draw_setup.stats,20);}
static void live_object_draw_setup_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002284){
  uint8_t object[164],record[16];uint32_t matrix[12],sp=cpu->gprs[13];
  live_object_draw_setup.active=0;live_object_draw_setup.stats[0]++;live_object_draw_setup.address=cpu->gprs[6];
  if(!native_surface_read(NULL,cpu->gprs[6],live_object_draw_setup.state,256)||!native_surface_read(NULL,cpu->gprs[7],object,164)||!native_surface_read(NULL,rd32(sp+0x24),record,16)||!native_surface_read(NULL,rd32(sp+0x14),matrix,48)||!nfs_visibility_object_draw_setup(live_object_draw_setup.state,record,object,matrix,live_object_draw_setup.xyz)){live_object_draw_setup.stats[3]++;return;}
  if((object[10]&16)!=0)live_object_draw_setup.stats[4]++;
  live_object_draw_setup.active=1;
 }
 if(pc==0x03002320&&live_object_draw_setup.active){
  uint8_t state[256];uint32_t sp=cpu->gprs[13];live_object_draw_setup.active=0;
  if(!native_surface_read(NULL,live_object_draw_setup.address,state,256)||memcmp(state,live_object_draw_setup.state,256)||rd32(sp+0x10)!=live_object_draw_setup.xyz[0]||rd32(sp+0xc)!=live_object_draw_setup.xyz[1]||rd32(sp+8)!=live_object_draw_setup.xyz[2])live_object_draw_setup.stats[2]++;
  else live_object_draw_setup.stats[1]++;
 }
}

static struct {unsigned active,expected;uint32_t stats[6];} live_object_visible;
API void nf_live_object_visible_stats(uint32_t out[6]){if(out)memcpy(out,live_object_visible.stats,24);}
static void live_object_visible_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002368){
  uint32_t sp=cpu->gprs[13],p[6]={rd32(sp+12),cpu->gprs[12],rd32(sp+24),rd32(sp+28),cpu->gprs[8],cpu->gprs[10]};
  live_object_visible.stats[0]++;live_object_visible.active=0;
  int result=nfs_visibility_object_visible(p,live_visibility.reciprocal);
  if(result<0){live_object_visible.stats[3]++;return;}
  live_object_visible.expected=result;live_object_visible.active=1;
 }
 if(live_object_visible.active&&(pc==0x030023b8||pc==0x0300262c)){
  unsigned visible=pc==0x030023b8;live_object_visible.active=0;
  live_object_visible.stats[visible?4:5]++;
  if(visible==live_object_visible.expected)live_object_visible.stats[1]++;else live_object_visible.stats[2]++;
 }
}

static struct {uint8_t object[164];uint32_t out[2],address,stats[5];unsigned active;} live_object_material;
API void nf_live_object_material_stats(uint32_t out[5]){if(out)memcpy(out,live_object_material.stats,20);}
static void live_object_material_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x030023b8){
  live_object_material.active=0;live_object_material.stats[0]++;live_object_material.address=cpu->gprs[7];
  if(!native_surface_read(NULL,cpu->gprs[7],live_object_material.object,164)||!nfs_visibility_object_material(live_object_material.object,rd32(cpu->gprs[6]+0x24),cpu->gprs[12],live_object_material.out)){live_object_material.stats[3]++;return;}
  if(live_object_material.out[1]!=(unsigned)cpu->gprs[12])live_object_material.stats[4]++;
  live_object_material.active=1;
 }
 if(pc==0x03002410&&live_object_material.active){
  uint8_t actual[164];live_object_material.active=0;
  if(!native_surface_read(NULL,live_object_material.address,actual,164)||memcmp(actual,live_object_material.object,164)||live_object_material.out[0]!=(unsigned)cpu->gprs[4]||live_object_material.out[1]!=(unsigned)cpu->gprs[12])live_object_material.stats[2]++;
  else live_object_material.stats[1]++;
 }
}

static struct {uint32_t out[2],stats[6];unsigned active;} live_object_texture;
API void nf_live_object_texture_stats(uint32_t out[6]){if(out)memcpy(out,live_object_texture.stats,24);}
static void live_object_texture_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002410){
  uint8_t object[164],material[32],previous[32];const uint8_t*prior=NULL;
  live_object_texture.active=0;live_object_texture.stats[0]++;
  if(!native_surface_read(NULL,cpu->gprs[7],object,164)||!native_surface_read(NULL,cpu->gprs[4],material,32))goto failed;
  if((object[10]&8)&&(int32_t)cpu->gprs[12]>1024){
   if((unsigned)cpu->gprs[4]<32||!native_surface_read(NULL,cpu->gprs[4]-32,previous,32))goto failed;
   prior=previous;
  }
  if(!nfs_visibility_object_texture(object,material,prior,rd32(cpu->gprs[6]+4),cpu->gprs[12],live_object_texture.out))goto failed;
  live_object_texture.active=1;
 }
 if(live_object_texture.active&&(pc==0x03002460||pc==0x03002588)){
  unsigned branch=pc==0x03002460;live_object_texture.active=0;live_object_texture.stats[branch?4:5]++;
  if(branch!=live_object_texture.out[1]||rd32(cpu->gprs[13]+4)!=live_object_texture.out[0])live_object_texture.stats[2]++;else live_object_texture.stats[1]++;
 }
 return;
 failed:live_object_texture.stats[3]++;
}

static struct {uint64_t epoch;unsigned serial,frame,object,verified;uint8_t context[68];uint32_t address,stats[6];unsigned active,expected;} live_object_model_context;
API void nf_live_object_model_context_stats(uint32_t out[6]){if(out)memcpy(out,live_object_model_context.stats,24);}
static void live_object_model_context_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled)return;
 if(pc==0x03002588){
  uint8_t state[256],object[164],material[32];uint32_t sp=cpu->gprs[13],p[4]={cpu->gprs[12],rd32(sp),rd32(sp+4),rd32(sp+24)};
  live_object_model_context.verified=0;live_object_model_context.epoch=live_scene_epoch;live_object_model_context.serial=live_scene.serial;live_object_model_context.frame=c->frameCounter(c);live_object_model_context.object=cpu->gprs[7];
  live_object_model_context.active=0;live_object_model_context.stats[0]++;live_object_model_context.address=sp+0x48;
  if(!native_surface_read(NULL,cpu->gprs[6],state,256)||!native_surface_read(NULL,cpu->gprs[7],object,164)||!native_surface_read(NULL,cpu->gprs[4],material,32)||!native_surface_read(NULL,sp+0x48,live_object_model_context.context,68))goto failed;
  int result=nfs_visibility_object_model_context(state,object,material,p,native_surface_read,NULL,live_object_model_context.context);
  if(result<0)goto failed;
  live_object_model_context.expected=result;live_object_model_context.active=1;
 }
 if(live_object_model_context.active&&(pc==0x03002628||pc==0x0300262c)){
  uint8_t actual[68];unsigned ready=pc==0x03002628;live_object_model_context.active=0;live_object_model_context.stats[ready?4:5]++;
  if(ready!=live_object_model_context.expected||!native_surface_read(NULL,live_object_model_context.address,actual,68)||memcmp(actual,live_object_model_context.context,68))live_object_model_context.stats[2]++;else {live_object_model_context.stats[1]++;live_object_model_context.verified=ready;}
 }
 return;
 failed:live_object_model_context.stats[3]++;
}

static uint32_t live_native_context_extract_stats[4];
API void nf_live_native_context_extract_stats(uint32_t out[4]){if(out)memcpy(out,live_native_context_extract_stats,16);}

static struct {uint32_t ranges[128][3],count,overflow;uint64_t reads,bytes;} live_model_reads;
API void nf_live_model_read_ranges(uint32_t out[128][3],uint32_t meta[2],uint64_t totals[2]){if(out)memcpy(out,live_model_reads.ranges,sizeof(live_model_reads.ranges));if(meta){meta[0]=live_model_reads.count;meta[1]=live_model_reads.overflow;}if(totals){totals[0]=live_model_reads.reads;totals[1]=live_model_reads.bytes;}}

typedef struct {uint8_t bytes[262144];uint32_t blocks[128][3],count,used,args[3],state,stats[4];int32_t rotation[12];size_t size;uint64_t hash,epoch;unsigned ready;} NFLiveOwnedModel;
typedef struct {uint32_t identity[5];uint8_t inputs[560];size_t size;uint64_t hash;} NFLiveModelInputs;
/* Bounded diagnostic ownership of actual per-draw frontend views. */
typedef struct {uint32_t kind,source;uint8_t palette[512];uint32_t refresh,vcount;} NFDrawWorldPalette;
static struct {NFDrawWorldPalette draws[128];uint64_t cycles[128];unsigned count,failed;} pending_world_palettes;
static struct {NFDrawWorldPalette draws[128];uint64_t cycles[128],epoch;uint32_t serial;unsigned count,failed;} completed_world_palettes[16];
static int draw_owned_capture_mode(void){unsigned mode=rd32(0x03005f14),frontend=c->busRead8(c,0x03006710);return (mode==1&&frontend==13)||((live_source_world_capture||getenv("NF_TEST_RACING_OWNED_CAPTURE"))&&mode==5&&frontend==4);}
static void draw_world_palette_capture(unsigned kind,unsigned source){
 if(!live_model_views_requested()||!draw_owned_capture_mode())return;
 if(pending_world_palettes.count>=128){pending_world_palettes.failed=1;return;}pending_world_palettes.cycles[pending_world_palettes.count]=mTimingGlobalTime(c->timing);NFDrawWorldPalette*draw=pending_world_palettes.draws+pending_world_palettes.count++;
 draw->kind=kind;draw->source=source;draw->refresh=c->frameCounter(c);draw->vcount=c->busRead16(c,0x04000006);if(!native_surface_read(NULL,0x05000000,draw->palette,512))pending_world_palettes.failed=1;
}
static NFVisibilitySnapshot*draw_builder_current;static unsigned draw_builder_verified;static uint32_t draw_builder_state;
static struct {NFVisibilitySnapshot*views[4],*roots[4],*builders[4],*current_root;uint32_t current_root_timing[3];uint64_t current_root_cycles,cycles[4][2];uint32_t model_args[4][3],states[4],timing[4][6];uint8_t model_inputs[4][560],root_palettes[4][512],current_root_palette[512];unsigned count,failed;} pending_draw_views;
static struct {NFVisibilitySnapshot*views[4],*roots[4],*builders[4];uint32_t model_args[4][3],states[4],timing[4][6];uint8_t model_inputs[4][560],root_palettes[4][512];uint64_t cycles[4][2],epoch;uint32_t serial,begin,end,page;unsigned count,failed;} completed_draw_views[16];
/* Capture completeness diagnostic; no source acceptance bypass. */
API int nf_live_completed_capture_detail(uint64_t epoch,uint32_t serial,uint32_t out[8]){unsigned slot=serial%16;if(!out||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial)return 0;uint32_t detail[8]={completed_draw_views[slot].count,completed_draw_views[slot].failed,completed_world_palettes[slot].count,completed_world_palettes[slot].failed,0,0,0,0};for(unsigned i=0;i<completed_draw_views[slot].count;i++){detail[4]+=completed_draw_views[slot].roots[i]!=NULL;detail[5]+=completed_draw_views[slot].builders[i]!=NULL;detail[6]+=completed_draw_views[slot].views[i]!=NULL;}detail[7]=completed_draw_views[slot].page;memcpy(out,detail,32);return 1;}
static void draw_views_pending_clear(void){for(unsigned i=0;i<pending_draw_views.count;i++)nf_visibility_snapshot_destroy(pending_draw_views.builders[i]);for(unsigned i=0;i<pending_draw_views.count;i++)nf_visibility_snapshot_destroy(pending_draw_views.views[i]);for(unsigned i=0;i<pending_draw_views.count;i++)nf_visibility_snapshot_destroy(pending_draw_views.roots[i]);nf_visibility_snapshot_destroy(pending_draw_views.current_root);memset(&pending_draw_views,0,sizeof(pending_draw_views));}
static void draw_views_close(void){nf_visibility_snapshot_destroy(draw_builder_current);draw_builder_current=NULL;draw_builder_verified=0;draw_views_pending_clear();for(unsigned j=0;j<16;j++){for(unsigned i=0;i<completed_draw_views[j].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[j].builders[i]);for(unsigned i=0;i<completed_draw_views[j].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[j].views[i]);for(unsigned i=0;i<completed_draw_views[j].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[j].roots[i]);memset(completed_draw_views+j,0,sizeof(completed_draw_views[j]));}}
/* Owned original BG-palette chronology, not an interpolated material policy. */
API int nf_live_completed_draw_palette_timeline(uint64_t epoch,uint32_t serial,unsigned ordinal,uint8_t root_palette[512],NFDrawWorldPalette*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(!root_palette||!out||!count||capacity<128||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count||completed_world_palettes[slot].failed||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial)return 0;
 unsigned begin=ordinal?completed_draw_views[slot].timing[ordinal-1][5]:0,end=completed_draw_views[slot].timing[ordinal][5];if(begin>end||end>completed_world_palettes[slot].count)return 0;
 memcpy(root_palette,completed_draw_views[slot].root_palettes[ordinal],512);memcpy(out,completed_world_palettes[slot].draws+begin,(end-begin)*sizeof(*out));*count=end-begin;return 1;
}
/* Parallel chronology array preserves the public palette record ABI. */
API int nf_live_completed_world_cycles(uint64_t epoch,uint32_t serial,unsigned pass,uint64_t*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;
 if(!out||!count||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||pass>=completed_draw_views[slot].count||completed_world_palettes[slot].failed||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial)return 0;
 unsigned begin=pass?completed_draw_views[slot].timing[pass-1][5]:0,end=completed_draw_views[slot].timing[pass][5];
 if(begin>end||end>completed_world_palettes[slot].count||capacity<end-begin)return 0;
 memcpy(out,completed_world_palettes[slot].cycles+begin,(end-begin)*sizeof(*out));*count=end-begin;return 1;
}
/* Original root/model entry times; not estimated from refresh boundaries. */
API int nf_live_completed_draw_cycles(uint64_t epoch,uint32_t serial,unsigned ordinal,uint64_t out[2]){
 unsigned slot=serial%16;if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 memcpy(out,completed_draw_views[slot].cycles[ordinal],16);return 1;
}
API int nf_live_completed_draw_timing(uint64_t epoch,uint32_t serial,unsigned ordinal,uint32_t out[6]){
 unsigned slot=serial%16;if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;memcpy(out,completed_draw_views[slot].timing[ordinal],24);return 1;
}
API int nf_live_completed_draw_view(uint64_t epoch,uint32_t serial,unsigned ordinal,uint32_t out[12]){
 unsigned slot=serial%16;if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_prepared_view(completed_draw_views[slot].views[ordinal],out);
}
API int nf_live_completed_draw_root(uint64_t epoch,uint32_t serial,unsigned ordinal,uint32_t out[12],NFVisibilityResult*result){
 unsigned slot=serial%16;if(!out||!result||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 NFVisibilityResult evaluated;uint32_t view[12];NFVisibilitySnapshot*root=completed_draw_views[slot].roots[ordinal];
 if(!nf_visibility_snapshot_prepared_view(root,view)||!nf_visibility_snapshot_evaluate(root,&evaluated))return 0;memcpy(out,view,48);memcpy(result,&evaluated,sizeof(evaluated));return 1;
}
API int nf_live_completed_draw_root_captured(uint64_t epoch,uint32_t serial,unsigned ordinal,NFVisibilityResult*out){
 unsigned slot=serial%16;if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 NFVisibilitySnapshot*root=completed_draw_views[slot].roots[ordinal];NFVisibilityResult result;uint32_t queue,groups;
 if(!nf_visibility_snapshot_read(root,completed_draw_views[slot].states[ordinal],result.state,256))return 0;memcpy(&queue,result.state+96,4);memcpy(&groups,result.state+100,4);
 if(!nf_visibility_snapshot_read(root,queue,result.queue,NF_VISIBILITY_QUEUE_BYTES)||!nf_visibility_snapshot_read(root,groups,result.groups,4096))return 0;
 /* Selected is independently retained in snapshot evaluation; compare state/queue/groups. */
 result.selected=0;memcpy(out,&result,sizeof(result));return 1;
}
void nf_visibility_snapshot_prepared_command_detail(uint32_t out[8]);
API void nf_live_scene_planner_detail(uint32_t out[18]){nf_scene_command_plan_detail(out);}
API void nf_live_prepared_command_detail(uint32_t out[8]){nf_visibility_snapshot_prepared_command_detail(out);}
API int nf_live_completed_draw_root_commands(uint64_t epoch,uint32_t serial,unsigned ordinal,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_prepared_builder_commands(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].builders[ordinal],out,capacity,count);
}
/* Immutable references into the identity-checked publication's owned assets.
   type1/2=copy/fill, type3=world, type4=model; ordinal is operation or command. */

static uint32_t operation_order_detail[8];
API void nf_live_operation_order_detail(uint32_t out[8]){if(out)memcpy(out,operation_order_detail,32);}
API int nf_live_completed_operation_order(uint64_t epoch,uint32_t serial,NFOrderedSceneEvent*out,unsigned capacity,unsigned*count){
 memset(operation_order_detail,0,32);operation_order_detail[0]=1;unsigned slot=serial%16,n=0;NFOrderedSceneEvent events[608];
 if(!out||!count||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||!completed_draw_views[slot].count||completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].failed||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial||completed_world_palettes[slot].failed)return 0;
 operation_order_detail[0]=2;uint32_t page=completed_draw_views[slot].page;
 for(unsigned i=0;i<completed_indexed_copies[slot].count;i++){
  NFOwnedCopyEvent*e=completed_indexed_copies[slot].events+i;uint32_t kind,p,offset;const uint8_t*indices;size_t bytes;
  int operation_valid=nf_indexed_operation_view(e->asset,e->size,&kind,&p,&offset,&indices,&bytes);if(!operation_valid||p!=page){operation_order_detail[0]=5;operation_order_detail[1]=i;operation_order_detail[2]=operation_valid;operation_order_detail[3]=operation_valid?p:UINT32_MAX;operation_order_detail[4]=page;operation_order_detail[5]=e->refresh;operation_order_detail[6]=e->caller;operation_order_detail[7]=e->kind;return 0;}
  events[n++]=(NFOrderedSceneEvent){e->cycles,kind,0xffffffffu,i,kind,0,p};
 }
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;int ok=1;
 for(unsigned pass=0;pass<completed_draw_views[slot].count&&ok;pass++){
  unsigned amount=0,begin=pass?completed_draw_views[slot].timing[pass-1][5]:0,end=pass+1==completed_draw_views[slot].count?completed_world_palettes[slot].count:completed_draw_views[slot].timing[pass][5],world=begin,models=0;
  ok=begin<=end&&end<=completed_world_palettes[slot].count&&nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&amount);
  for(unsigned i=0;i<amount&&ok;i++){
   NFNativeSceneCommand*c=commands+i;uint64_t cycles=0;unsigned type=0;
   if(c->kind==1||c->kind==2){
    if(world>=end||c->kind!=completed_world_palettes[slot].draws[world].kind||c->source!=completed_world_palettes[slot].draws[world].source){operation_order_detail[0]=3;operation_order_detail[1]=pass;operation_order_detail[2]=i;operation_order_detail[3]=world;operation_order_detail[4]=c->kind;operation_order_detail[5]=c->source;if(world<end){operation_order_detail[6]=completed_world_palettes[slot].draws[world].kind;operation_order_detail[7]=completed_world_palettes[slot].draws[world].source;}ok=0;break;}
    cycles=completed_world_palettes[slot].cycles[world++];type=3;
   }else if(c->kind==5){cycles=completed_draw_views[slot].cycles[pass][1];type=4;models++;}else{ok=0;break;}
   if(!cycles||n>=608){ok=0;break;}events[n++]=(NFOrderedSceneEvent){cycles,type,pass,i,c->kind,c->source,page};
  }
  if(ok&&(world!=end||models!=1)){operation_order_detail[0]=4;operation_order_detail[1]=world;operation_order_detail[2]=end;operation_order_detail[3]=models;ok=0;}
 }
 free(commands);if(!ok||capacity<n)return 0;
 for(unsigned i=1;i<n;i++){NFOrderedSceneEvent e=events[i];unsigned j=i;while(j&&events[j-1].cycles>e.cycles){events[j]=events[j-1];j--;}events[j]=e;}
 for(unsigned i=1;i<n;i++)if(events[i-1].cycles>=events[i].cycles)return 0;
 memcpy(out,events,n*sizeof(*out));*count=n;return 1;
}
/* Source geometry coverage, independently of GPU projected polygons. */
API int nf_live_completed_draw_road_spans(uint64_t epoch,uint32_t serial,unsigned pass,unsigned ordinal,uint32_t*out,unsigned capacity,unsigned*count){
 if(!out||!count)return 0;NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;
 unsigned n=0,amount=0;uint32_t spans[512*4],framebuffer[4],address;uint16_t inherited[4];
 int ok=nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&n)&&ordinal<n&&commands[ordinal].kind==1;
 if(ok){NFNativeSceneCommand*cmd=commands+ordinal;memcpy(&address,cmd->state+80,4);memcpy(inherited,cmd->record+2,8);
  ok=nf_visibility_snapshot_read(completed_draw_views[serial%16].roots[pass],address,framebuffer,16)&&nf_road_span_plan(cmd->vertices,cmd->vertex_count,inherited[2],inherited[3],cmd->xyz[0],cmd->xyz[1],live_visibility.reciprocal,framebuffer,spans,512,&amount)&&capacity>=amount;
 }
 free(commands);if(!ok)return 0;memcpy(out,spans,amount*16);*count=amount;return 1;
}
static int owned_span_read(void*reader,uint32_t address,void*out,size_t size){return nf_visibility_snapshot_read(reader,address,out,size);}
/* Primary-road material contexts only. Secondary layer must be resolved
   explicitly rather than silently reusing the primary descriptor. */
/* Internal caller supplies commands rebuilt from this exact immutable root/pass. */
static int completed_road_contexts_command(uint32_t serial,unsigned pass,const NFNativeSceneCommand*cmd,uint32_t*out,unsigned capacity,unsigned*count){
 if(!cmd||!out||!count||cmd->kind!=1||cmd->xyz[2])return 0;
 unsigned amount=0;uint32_t spans[512*20],framebuffer[4],address,seed[16];uint16_t inherited[4];uint8_t descriptor[48];
 NFVisibilitySnapshot*root=completed_draw_views[serial%16].roots[pass];memcpy(&address,cmd->state+80,4);memcpy(inherited,cmd->record+2,8);
 if(!owned_span_read(root,address,framebuffer,16)||!owned_span_read(root,cmd->source,descriptor,48)||!nf_road_material_seed(cmd->state,descriptor,owned_span_read,root,seed)||!nf_road_span_contexts(cmd->vertices,cmd->vertex_count,inherited[2],inherited[3],cmd->xyz[0],cmd->xyz[1],live_visibility.reciprocal,framebuffer,seed,spans,512,&amount)||capacity<amount)return 0;
 memcpy(out,spans,amount*80);*count=amount;return 1;
}
API int nf_live_completed_draw_road_contexts(uint64_t epoch,uint32_t serial,unsigned pass,unsigned ordinal,uint32_t*out,unsigned capacity,unsigned*count){
 if(!out||!count)return 0;NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned n=0;
 int ok=nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&n)&&ordinal<n&&completed_road_contexts_command(serial,pass,commands+ordinal,out,capacity,count);
 free(commands);return ok;
}
/* NFRE v1: owned primary road span contexts and packed source texture.
   Header10 words, spans20 words each, then texture bytes; no VRAM reads. */
static int completed_road_asset_from_contexts(uint32_t serial,unsigned pass,unsigned ordinal,const uint32_t*spans,unsigned count,void**out,size_t*size){
 if(!out||!size||!spans||!count||count>512)return 0;
 const uint32_t*ctx=spans+4;uint32_t width=(ctx[1]>>16)+1,height=(ctx[2]>>16)+1;
 size_t bytes=nf_road_texture_extent(ctx[0],ctx[1],ctx[2]);
 if(ctx[0]>16||!bytes||bytes>1024*1024||ctx[5]<0x08000000||ctx[5]>=0x0a000000||bytes>0x0a000000-ctx[5])return 0;
 for(unsigned i=0;i<count;i++){const uint32_t*c=spans+i*20+4;if(c[0]!=ctx[0]||c[1]!=ctx[1]||c[2]!=ctx[2]||c[5]!=ctx[5])return 0;}
 size_t total=40+(size_t)count*80+bytes;uint8_t*asset=malloc(total);if(!asset)return 0;
 uint32_t header[10]={0x4552464e,1,serial,pass,ordinal,count,ctx[0],ctx[5],(uint32_t)bytes,40+count*80};
 memcpy(asset,header,40);memcpy(asset+40,spans,count*80);
 if(!owned_span_read(completed_draw_views[serial%16].roots[pass],ctx[5],asset+header[9],bytes)){free(asset);return 0;}
 NFRoadAssetView checked;if(!nf_road_asset_view(asset,total,&checked)){free(asset);return 0;}
 *out=asset;*size=total;return 1;
}
API int nf_live_completed_draw_road_asset(uint64_t epoch,uint32_t serial,unsigned pass,unsigned ordinal,void**out,size_t*size){
 uint32_t spans[512*20];unsigned count=0;if(!out||!size||!nf_live_completed_draw_road_contexts(epoch,serial,pass,ordinal,spans,512,&count))return 0;
 return completed_road_asset_from_contexts(serial,pass,ordinal,spans,count,out,size);
}
API int nf_live_road_asset_validate(const void*data,size_t size){NFRoadAssetView view;return nf_road_asset_view(data,size,&view);}
static int road_asset_texture_read(void*context,uint32_t address,void*out,size_t size){
 NFRoadAssetView*v=context;if(address<v->header[7])return 0;size_t offset=address-v->header[7];
 if(offset>v->header[8]||size>v->header[8]-offset)return 0;memcpy(out,v->texture+offset,size);return 1;
}
/* Diagnostic native material sampling, no framebuffer access or writes.
   Both recovered affine and perspective writers use owned texture data. */
API int nf_live_road_asset_span_pixels(const void*asset,size_t size,unsigned ordinal,const uint32_t*reciprocal,uint16_t*out,unsigned capacity){
 NFRoadAssetView view;if(!out||!reciprocal||!nf_road_asset_view(asset,size,&view)||ordinal>=view.header[5])return 0;
 uint32_t span[20],runs[32*16],final[16];unsigned count=0;memcpy(span,view.spans+ordinal*80,80);
 if(capacity<span[1])return 0;
 if(span[2]==0x03003190){if(!nf_road_perspective_plan(span+4,reciprocal,runs,32,&count,final))return 0;}
 else if(span[2]==0x030056d8){memcpy(runs,span+4,64);count=1;}else return 0;
 uint16_t pixels[512];unsigned used=0;
 for(unsigned i=0;i<count;i++){uint32_t*c=runs+i*16;if(c[7]>span[1]-used||!nf_road_span_pixels(c,road_asset_texture_read,&view,pixels+used,512-used))return 0;used+=c[7];}
 if(used!=span[1])return 0;memcpy(out,pixels,used*2);return 1;
}
API void nf_live_road_asset_free(void*asset){free(asset);}
API int nf_live_completed_draw_root_commands_view(uint64_t epoch,uint32_t serial,unsigned ordinal,const uint32_t view[12],NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(!view||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_prepared_builder_commands_view(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].builders[ordinal],view,out,capacity,count);
}
/* Camera metadata follows native command order, including repeated objects. */
API int nf_live_completed_draw_root_cameras(uint64_t epoch,uint32_t serial,unsigned ordinal,NFRigidPose*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(!out||!count||capacity<144||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 NFVisibilitySnapshot*root=completed_draw_views[slot].roots[ordinal];uint32_t view[12];NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));unsigned n=0;NFRigidPose camera;
 int ok=commands&&nf_visibility_snapshot_prepared_view(root,view)&&nf_visibility_snapshot_prepared_builder_commands(root,completed_draw_views[slot].builders[ordinal],commands,144,&n);
 if(ok){NFPoint3 position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};ok=nf_pose_decode((const int32_t*)view,&position,&camera);}
 if(ok){for(unsigned i=0;i<n;i++)out[i]=camera;*count=n;}free(commands);return ok;
}
/* Pair only the same retained draw occurrences and command topology. */
API int nf_live_completed_draw_camera_pair(uint64_t epoch,uint32_t older,uint32_t newer,NFRigidPose*a,NFRigidPose*b,unsigned capacity,unsigned*count){
 unsigned sa=older%16,sb=newer%16;if(!a||!b||a==b||!count||capacity<144||older>=newer||epoch!=live_scene_epoch||completed_draw_views[sa].epoch!=epoch||completed_draw_views[sb].epoch!=epoch||completed_draw_views[sa].serial!=older||completed_draw_views[sb].serial!=newer||completed_draw_views[sa].failed||completed_draw_views[sb].failed||!completed_draw_views[sa].count||completed_draw_views[sa].count!=completed_draw_views[sb].count)return 0;
 NFNativeSceneCommand*left=malloc(144*sizeof(*left)),*right=malloc(144*sizeof(*right));NFRigidPose ca[144],cb[144];unsigned total=0;int ok=left&&right;
 for(unsigned pass=0;ok&&pass<completed_draw_views[sa].count;pass++){
  unsigned na=0,nb=0,nca=0,ncb=0;ok=completed_draw_views[sa].states[pass]==completed_draw_views[sb].states[pass]&&nf_live_completed_draw_root_commands(epoch,older,pass,left,144,&na)&&nf_live_completed_draw_root_commands(epoch,newer,pass,right,144,&nb)&&na==nb&&total+na<=144;
  for(unsigned j=0;ok&&j<na;j++)ok=left[j].kind==right[j].kind&&left[j].source==right[j].source&&left[j].object==right[j].object&&left[j].owner==right[j].owner&&left[j].pass==right[j].pass;
  if(ok)ok=nf_live_completed_draw_root_cameras(epoch,older,pass,ca+total,144,&nca)&&nf_live_completed_draw_root_cameras(epoch,newer,pass,cb+total,144,&ncb)&&nca==na&&ncb==nb;
  if(ok)total+=na;
 }free(left);free(right);if(!ok||!total)return 0;memcpy(a,ca,total*sizeof(*a));memcpy(b,cb,total*sizeof(*b));*count=total;return 1;
}
API int nf_live_completed_draw_builder_result(uint64_t epoch,uint32_t serial,unsigned ordinal,NFVisibilityResult*out){
 unsigned slot=serial%16;if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_evaluate(completed_draw_views[slot].builders[ordinal],out);
}
API int nf_live_completed_draw_root_captured_commands(uint64_t epoch,uint32_t serial,unsigned ordinal,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_prepared_captured_commands(completed_draw_views[slot].roots[ordinal],out,capacity,count);
}
static int draw_root_asset_read(void*user,uint32_t address,void*out,size_t size){return nf_visibility_snapshot_read(user,address,out,size);}
static uint32_t draw_root_asset_detail[7];
API void nf_live_draw_root_asset_detail(uint32_t out[7]){if(out)memcpy(out,draw_root_asset_detail,sizeof(draw_root_asset_detail));}
/* Exact immutable root and chronological surface palette supplied by scene builder. */
static int draw_root_asset_command(uint64_t epoch,uint32_t serial,unsigned pass,unsigned palette_index,const NFNativeSceneCommand*command,void**asset,size_t*asset_size,void**light,size_t*light_size){
 unsigned slot=serial%16;if(!command||!asset||!asset_size||!light||!light_size||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||pass>=completed_draw_views[slot].count||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial||completed_world_palettes[slot].failed||(command->kind!=1&&command->kind!=2)||palette_index>=completed_world_palettes[slot].count)return 0;
 NFDrawWorldPalette*draw=completed_world_palettes[slot].draws+palette_index;unsigned detail=0;
 return draw->kind==command->kind&&draw->source==command->source&&nf_extract_scene_command_full(command,draw_root_asset_read,completed_draw_views[slot].roots[pass],draw->palette,NULL,asset,asset_size,light,light_size,&detail);
}
API int nf_live_completed_draw_root_asset(uint64_t epoch,uint32_t serial,unsigned ordinal,unsigned index,void**asset,size_t*asset_size,void**light,size_t*light_size){
 unsigned slot=serial%16;if(epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial||completed_world_palettes[slot].failed)return 0;
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned count=0,palette_index=0;int ok=1;
 for(unsigned pass=0;pass<=ordinal&&ok;pass++){
  ok=nf_visibility_snapshot_prepared_builder_commands(completed_draw_views[slot].roots[pass],completed_draw_views[slot].builders[pass],commands,144,&count);
  if(!ok||(pass==ordinal&&index>=count)){ok=0;break;}
  unsigned limit=pass==ordinal?index:count;
  for(unsigned i=0;i<limit;i++)palette_index+=commands[i].kind==1||commands[i].kind==2;
 }
 if(ok){NFNativeSceneCommand*command=commands+index;memset(draw_root_asset_detail,0,sizeof(draw_root_asset_detail));draw_root_asset_detail[0]=palette_index;draw_root_asset_detail[1]=command->kind;draw_root_asset_detail[2]=command->source;draw_root_asset_detail[3]=completed_world_palettes[slot].count;if((command->kind!=1&&command->kind!=2)||palette_index>=completed_world_palettes[slot].count)ok=0;
  else {NFDrawWorldPalette*draw=completed_world_palettes[slot].draws+palette_index;draw_root_asset_detail[4]=draw->kind;draw_root_asset_detail[5]=draw->source;ok=draw->kind==command->kind&&draw->source==command->source&&nf_extract_scene_command_full(command,draw_root_asset_read,completed_draw_views[slot].roots[ordinal],draw->palette,NULL,asset,asset_size,light,light_size,draw_root_asset_detail+6);}}
 free(commands);return ok;
}
/* Owned NWI1 payload for one native command, suitable for ordered assembly. */
static int draw_wall_index_metadata(const NFNativeSceneCommand*c,NFReadMemory read,void*reader,uint8_t**data,uint32_t width,uint32_t height,uint32_t planes,size_t*bytes,unsigned*mode){
 if(!getenv("NF_CAPTURE_WALL_OUTPUT_INDICES"))return 1;
 uint8_t*indices=NULL;uint32_t iw=0,ih=0,ip=0;
 if(!nf_scene_command_wall_indices_owned(c,read,reader,&indices,&iw,&ih,&ip))return 0;
 int ok=iw==width&&ih==height&&ip==planes;size_t size=(size_t)width*height*planes;
 uint8_t*paired=ok?malloc(size*2):NULL;if(!paired)ok=0;
 if(ok){memcpy(paired,*data,size);memcpy(paired+size,indices,size);free(*data);*data=paired;*bytes=size*2;*mode=planes==17?8:7;}
 free(indices);return ok;
}
API int nf_live_completed_draw_root_commands_focal(uint64_t epoch,uint32_t serial,unsigned ordinal,const uint32_t view[12],uint32_t focal,uint32_t builder_focal,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 unsigned slot=serial%16;if(!view||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 return nf_visibility_snapshot_prepared_builder_commands_focal(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].builders[ordinal],view,focal,builder_focal,0,NULL,out,capacity,count);
}
/* Rebuild primary road terminal spans from owned sampled-view commands.
   Never borrow original projected spans for a moving camera. Focal values0
   select the source basis; explicit sampled focals use the focal builder. */
static uint32_t sampled_road_asset_detail[4];
API void nf_live_completed_draw_road_asset_view_detail(uint32_t out[4]){if(out)memcpy(out,sampled_road_asset_detail,16);}
API int nf_live_completed_draw_road_asset_view(uint64_t epoch,uint32_t serial,unsigned pass,unsigned ordinal,const uint32_t view[12],uint32_t focal,uint32_t builder_focal,void**out,size_t*size){
 memset(sampled_road_asset_detail,0,sizeof(sampled_road_asset_detail));sampled_road_asset_detail[0]=1;
 if(!view||!out||!size||!!focal!=!!builder_focal)return 0;
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned n=0,amount=0;uint32_t spans[512*20],framebuffer[4],address,seed[16];uint16_t inherited[4];uint8_t descriptor[48];
 int ok=(focal?nf_live_completed_draw_root_commands_focal(epoch,serial,pass,view,focal,builder_focal,commands,144,&n):nf_live_completed_draw_root_commands_view(epoch,serial,pass,view,commands,144,&n))&&ordinal<n&&commands[ordinal].kind==1&&!commands[ordinal].xyz[2];
 sampled_road_asset_detail[0]=2;if(ordinal<n){sampled_road_asset_detail[1]=commands[ordinal].kind;sampled_road_asset_detail[2]=commands[ordinal].xyz[2];}
 void*asset=NULL;size_t bytes=0;
 if(ok){NFNativeSceneCommand*cmd=commands+ordinal;NFVisibilitySnapshot*root=completed_draw_views[serial%16].roots[pass];memcpy(&address,cmd->state+80,4);memcpy(inherited,cmd->record+2,8);
 sampled_road_asset_detail[0]=3;ok=owned_span_read(root,address,framebuffer,16)&&owned_span_read(root,cmd->source,descriptor,48);
 if(ok){sampled_road_asset_detail[0]=4;ok=nf_road_material_seed(cmd->state,descriptor,owned_span_read,root,seed);}
 if(ok){sampled_road_asset_detail[0]=5;ok=nf_road_span_contexts(cmd->vertices,cmd->vertex_count,inherited[2],inherited[3],cmd->xyz[0],cmd->xyz[1],live_visibility.reciprocal,framebuffer,seed,spans,512,&amount);sampled_road_asset_detail[3]=amount;}
 if(ok){sampled_road_asset_detail[0]=6;ok=amount&&completed_road_asset_from_contexts(serial,pass,ordinal,spans,amount,&asset,&bytes);}

 }
 free(commands);if(!ok){free(asset);return 0;}*out=asset;*size=bytes;sampled_road_asset_detail[0]=7;return 1;
}

API int nf_live_completed_draw_builder_focal(uint64_t epoch,uint32_t serial,unsigned ordinal,uint32_t*out){
 unsigned slot=serial%16;uint8_t state[256];uint32_t address,value;
 if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||ordinal>=completed_draw_views[slot].count)return 0;
 NFVisibilityResult evaluated;if(!nf_visibility_snapshot_evaluate(completed_draw_views[slot].builders[ordinal],&evaluated))return 0;
 memcpy(&address,evaluated.state+80,4);if(!nf_visibility_snapshot_read(completed_draw_views[slot].builders[ordinal],address+28,&value,4))return 0;*out=value;return 1;
}
/* Internal exact-root command reuse; public wrapper still validates source identity. */
static int draw_root_metadata_command(NFVisibilitySnapshot*root,const NFNativeSceneCommand*c,void**out,size_t*size,unsigned*mode){
 if(!root||!c||!out||!size||!mode)return 0;uint8_t*data=NULL;size_t bytes=0;unsigned selected=0;uint32_t width,height,planes;int ok=1;
  if(c->kind==1){NFRoadSourceAttributes raw;ok=nf_scene_command_road_indices_owned(c,draw_root_asset_read,root,&data,&width,&height)&&nf_scene_command_road_attributes_owned(c,draw_root_asset_read,root,&raw);
   if(ok){bytes=(size_t)width*height;uint8_t*expanded=malloc(bytes+sizeof(raw));if(!expanded)ok=0;else{memcpy(expanded,data,bytes);memcpy(expanded+bytes,&raw,sizeof(raw));free(data);data=expanded;bytes+=sizeof(raw);selected=raw.affine?6:5;}}}
  else if(c->kind==2){ok=nf_scene_command_wall_states_owned(c,draw_root_asset_read,root,&data,&width,&height,&planes);if(ok){bytes=(size_t)width*height*planes;selected=planes==17?3:2;ok=draw_wall_index_metadata(c,draw_root_asset_read,root,&data,width,height,planes,&bytes,&selected);}}
  else ok=0;
 if(!ok){free(data);return 0;}*out=data;*size=bytes;*mode=selected;return 1;
}
API int nf_live_completed_draw_root_metadata(uint64_t epoch,uint32_t serial,unsigned ordinal,unsigned index,void**out,size_t*size,unsigned*mode){
 unsigned slot=serial%16;if(!out||!size||!mode||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned count=0;NFVisibilitySnapshot*root=completed_draw_views[slot].roots[ordinal];
 int ok=nf_visibility_snapshot_prepared_builder_commands(root,completed_draw_views[slot].builders[ordinal],commands,144,&count)&&index<count&&draw_root_metadata_command(root,commands+index,out,size,mode);free(commands);return ok;
}
typedef struct {NFVisibilitySnapshot*root;uint32_t address;const uint32_t*view;uint32_t projection,focal;} NFDrawViewReader;
static int draw_view_read(void*user,uint32_t address,void*out,size_t bytes){
 NFDrawViewReader*r=user;if(!nf_visibility_snapshot_read(r->root,address,out,bytes))return 0;uint64_t end=(uint64_t)address+bytes,view_end=(uint64_t)r->address+48;uint64_t lo=address>r->address?address:r->address,hi=end<view_end?end:view_end;if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)r->view+(size_t)(lo-r->address),(size_t)(hi-lo));
 if(r->focal){uint64_t start=(uint64_t)r->projection+28,limit=start+4;lo=address>start?address:start;hi=end<limit?end:limit;if(lo<hi)memcpy((uint8_t*)out+(size_t)(lo-address),(const uint8_t*)&r->focal+(size_t)(lo-start),(size_t)(hi-lo));}return 1;
}
/* Stable source topology only; all assets/metadata use the same sampled view. */
static int draw_world_view_extract(unsigned slot,unsigned ordinal,unsigned palette_index,const NFDrawWorldPalette*override,const NFNativeSceneCommand*c,const uint32_t view[12],uint32_t focal,void**asset,size_t*asset_size,void**light,size_t*light_size,void**metadata,size_t*metadata_size,unsigned*mode){
 int ok=completed_world_palettes[slot].epoch==completed_draw_views[slot].epoch&&completed_world_palettes[slot].serial==completed_draw_views[slot].serial&&!completed_world_palettes[slot].failed;
 void*owned=NULL,*illumination=NULL;uint8_t*data=NULL;size_t bytes=0,light_bytes=0,metadata_bytes=0;unsigned selected=0;uint32_t width=0,height=0,planes=0,detail=0;
 if(ok){NFDrawViewReader reader={completed_draw_views[slot].roots[ordinal],0,view};memcpy(&reader.address,c->state+84,4);memcpy(&reader.projection,c->state+80,4);reader.focal=focal;ok=(c->kind==1||c->kind==2)&&(override||palette_index<completed_world_palettes[slot].count);
  if(ok){const NFDrawWorldPalette*palette=override?override:completed_world_palettes[slot].draws+palette_index;ok=palette->kind==c->kind&&palette->source==c->source&&nf_extract_scene_command_full(c,draw_view_read,&reader,palette->palette,NULL,&owned,&bytes,&illumination,&light_bytes,&detail);}
  if(ok&&c->kind==1){NFRoadSourceAttributes raw;ok=nf_scene_command_road_indices_owned(c,draw_view_read,&reader,&data,&width,&height)&&nf_scene_command_road_attributes_owned(c,draw_view_read,&reader,&raw);if(ok){metadata_bytes=(size_t)width*height;uint8_t*expanded=malloc(metadata_bytes+sizeof(raw));if(!expanded)ok=0;else{memcpy(expanded,data,metadata_bytes);memcpy(expanded+metadata_bytes,&raw,sizeof(raw));free(data);data=expanded;metadata_bytes+=sizeof(raw);selected=raw.affine?6:5;}}}
  else if(ok){ok=nf_scene_command_wall_states_owned(c,draw_view_read,&reader,&data,&width,&height,&planes);if(ok){metadata_bytes=(size_t)width*height*planes;selected=planes==17?3:2;ok=draw_wall_index_metadata(c,draw_view_read,&reader,&data,width,height,planes,&metadata_bytes,&selected);}}
 }if(!ok){nf_surface_free(owned);nf_surface_free(illumination);free(data);return 0;}*asset=owned;*asset_size=bytes;*light=illumination;*light_size=light_bytes;*metadata=data;*metadata_size=metadata_bytes;*mode=selected;return 1;
}
API int nf_live_completed_draw_root_world_view(uint64_t epoch,uint32_t serial,unsigned ordinal,unsigned index,const uint32_t view[12],void**asset,size_t*asset_size,void**light,size_t*light_size,void**metadata,size_t*metadata_size,unsigned*mode){
 unsigned slot=serial%16;if(!view||!asset||!asset_size||!light||!light_size||!metadata||!metadata_size||!mode||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count||completed_world_palettes[slot].epoch!=epoch||completed_world_palettes[slot].serial!=serial||completed_world_palettes[slot].failed)return 0;
 NFNativeSceneCommand*original=malloc(144*sizeof(*original)),*sampled=malloc(144*sizeof(*sampled));unsigned count=0,sample_count=0,palette_index=0;int ok=original&&sampled;
 for(unsigned pass=0;ok&&pass<=ordinal;pass++){ok=nf_live_completed_draw_root_commands(epoch,serial,pass,original,144,&count);if(!ok||(pass==ordinal&&index>=count)){ok=0;break;}unsigned limit=pass==ordinal?index:count;for(unsigned j=0;j<limit;j++)palette_index+=original[j].kind==1||original[j].kind==2;}
 if(ok)ok=nf_live_completed_draw_root_commands_view(epoch,serial,ordinal,view,sampled,144,&sample_count)&&sample_count==count;
 for(unsigned j=0;ok&&j<count;j++)ok=original[j].kind==sampled[j].kind&&original[j].source==sampled[j].source&&original[j].object==sampled[j].object&&original[j].owner==sampled[j].owner&&original[j].pass==sampled[j].pass;
 if(ok)ok=draw_world_view_extract(slot,ordinal,palette_index,NULL,sampled+index,view,0,asset,asset_size,light,light_size,metadata,metadata_size,mode);free(original);free(sampled);return ok;
}
typedef struct {NFVisibilitySnapshot*snapshot;const uint8_t*palette;} NFDrawModelReader;
static int draw_model_asset_read(void*user,uint32_t address,void*out,size_t size){
 NFDrawModelReader*r=user;if(address>=0x05000000u&&address<0x05000200u){if((uint64_t)address+size>0x05000200u)return 0;memcpy(out,r->palette+address-0x05000000u,size);return 1;}return nf_visibility_snapshot_read(r->snapshot,address,out,size);
}
API int nf_live_completed_draw_model_asset(uint64_t epoch,uint32_t serial,unsigned ordinal,void**asset,size_t*size){
 unsigned slot=serial%16;if(!asset||!size||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 uint32_t*args=completed_draw_views[slot].model_args[ordinal];uint8_t*inputs=completed_draw_views[slot].model_inputs[ordinal];NFDrawModelReader reader={completed_draw_views[slot].views[ordinal],inputs+48};
 return nf_extract_model(draw_model_asset_read,&reader,args[0],args[1],args[2],(const int32_t*)inputs,asset,size);
}
API int nf_live_completed_draw_model_indexed_asset(uint64_t epoch,uint32_t serial,unsigned ordinal,void**out,size_t*size){
 if(!out||!size)return 0;void*asset=NULL,*tagged=NULL;size_t bytes=0,tagged_bytes=0;
 if(!nf_live_completed_draw_model_asset(epoch,serial,ordinal,&asset,&bytes))return 0;
 unsigned slot=serial%16;uint8_t context[68],*indices=NULL;uint32_t width,height;
 NFVisibilitySnapshot*view=completed_draw_views[slot].views[ordinal];
 int ok=nf_visibility_snapshot_read(view,completed_draw_views[slot].model_args[ordinal][0],context,sizeof(context))&&nf_model_texture_indices_owned(draw_root_asset_read,view,context,&indices,&width,&height)&&nf_scene_model_attach_indices((NFSceneSection){asset,bytes},indices,(size_t)width*height,&tagged,&tagged_bytes);
 free(indices);nf_surface_free(asset);if(!ok)return 0;*out=tagged;*size=tagged_bytes;return 1;
}
static int draw_scene_pass_pair(uint64_t epoch,uint32_t older,uint32_t newer){
 unsigned a=older%16,b=newer%16;if(older>=newer||epoch!=live_scene_epoch||completed_draw_views[a].epoch!=epoch||completed_draw_views[b].epoch!=epoch||completed_draw_views[a].serial!=older||completed_draw_views[b].serial!=newer||completed_draw_views[a].failed||completed_draw_views[b].failed||!completed_draw_views[a].count||completed_draw_views[a].count!=completed_draw_views[b].count)return 0;
 for(unsigned j=0;j<completed_draw_views[a].count;j++)if(completed_draw_views[a].states[j]!=completed_draw_views[b].states[j]||memcmp(completed_draw_views[a].model_args[j],completed_draw_views[b].model_args[j],12))return 0;return 1;
}
/* Original owned projection provenance; output remains atomic on failure. */
API int nf_live_completed_draw_projection(uint64_t epoch,uint32_t serial,unsigned ordinal,uint32_t out[6]){
 unsigned slot=serial%16;uint8_t state[256],root_projection[32],context[68],model_projection[32];uint32_t address,values[6];
 if(!out||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||ordinal>=completed_draw_views[slot].count)return 0;
 if(!nf_visibility_snapshot_read(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].states[ordinal],state,256))return 0;
 memcpy(&address,state+80,4);if(!nf_visibility_snapshot_read(completed_draw_views[slot].roots[ordinal],address,root_projection,32))return 0;
 if(!nf_visibility_snapshot_read(completed_draw_views[slot].views[ordinal],completed_draw_views[slot].model_args[ordinal][0],context,68))return 0;
 memcpy(&address,context+8,4);if(!nf_visibility_snapshot_read(completed_draw_views[slot].views[ordinal],address,model_projection,32))return 0;
 memcpy(values,root_projection+28,4);memcpy(values+1,context+64,4);memcpy(values+2,model_projection+28,4);
 uint16_t x,y;memcpy(&x,root_projection+8,2);memcpy(&y,root_projection+10,2);values[3]=x;values[4]=y;values[5]=completed_draw_views[slot].count;
 memcpy(out,values,sizeof(values));return 1;
}
/* Model-draw cameras are independent of root world-draw cameras. Match
   model topology, projection, geometry/UV and indexed texture; palette colors
   are discrete scene state and may differ between original endpoints. */
static int draw_sample_focals(uint64_t epoch,uint32_t older,uint32_t newer,unsigned ordinal,double alpha,uint32_t out[2]){
 uint32_t projection[2][6],endpoints[2][2];
 if(!nf_live_completed_draw_projection(epoch,older,ordinal,projection[0])||!nf_live_completed_draw_projection(epoch,newer,ordinal,projection[1])||projection[0][3]!=projection[1][3]||projection[0][4]!=projection[1][4])return 0;
 for(unsigned i=0;i<2;i++){if(projection[i][0]!=projection[i][1]||projection[i][0]!=projection[i][2])return 0;endpoints[i][0]=projection[i][0];if(!nf_live_completed_draw_builder_focal(epoch,i?newer:older,ordinal,endpoints[i]+1))return 0;}
 return nf_projection_focal_sample(endpoints[0],endpoints[1],alpha,out);
}
API int nf_live_completed_draw_sample_focals(uint64_t epoch,uint32_t older,uint32_t newer,unsigned pass,double alpha,uint32_t out[2]){uint32_t values[2];if(!out||older>=newer||!isfinite(alpha)||alpha<0||alpha>1||!draw_sample_focals(epoch,older,newer,pass,alpha,values))return 0;memcpy(out,values,8);return 1;}
API int nf_live_completed_draw_model_pose_pair(uint64_t epoch,uint32_t older,uint32_t newer,NFRigidPose*camera_a,NFRigidPose*camera_b,NFRigidPose*object_a,NFRigidPose*object_b,unsigned capacity,unsigned*count){
 if(!camera_a||!camera_b||!object_a||!object_b||!count||capacity<4||camera_a==camera_b||camera_a==object_a||camera_a==object_b||camera_b==object_a||camera_b==object_b||object_a==object_b)return 0;
 NFRigidPose ca[4],cb[4],oa[4],ob[4];
 if(!draw_scene_pass_pair(epoch,older,newer))return 0;
 unsigned slots[2]={older%16,newer%16},n=completed_draw_views[slots[0]].count;int ok=1,reason=0;
 for(unsigned pass=0;ok&&pass<n;pass++){
  reason=1;ok=!memcmp(completed_draw_views[slots[0]].model_args[pass],completed_draw_views[slots[1]].model_args[pass],12);
  void*a=NULL,*b=NULL;size_t na=0,nb=0;
  if(ok){reason=2;ok=nf_live_completed_draw_model_indexed_asset(epoch,older,pass,&a,&na)&&nf_live_completed_draw_model_indexed_asset(epoch,newer,pass,&b,&nb);}
  if(ok){const uint8_t*ia=NULL,*ib=NULL;size_t pixels_a=0,pixels_b=0;
   unsigned header=getenv("NF_TEST_FOCAL_SAMPLE")?40:48;uint32_t focals[2];
   reason=3;ok=na==nb&&na>=160&&!memcmp(a,b,header)&&(!getenv("NF_TEST_FOCAL_SAMPLE")||draw_sample_focals(epoch,older,newer,pass,.5,focals))&&nf_scene_model_indices((NFSceneSection){a,na},&ia,&pixels_a)&&nf_scene_model_indices((NFSceneSection){b,nb},&ib,&pixels_b)&&pixels_a==pixels_b;
   if(ok){reason=4;size_t geometry=(size_t)(ia-(uint8_t*)a)-16-pixels_a*4;ok=geometry>=160&&!memcmp((uint8_t*)a+160,(uint8_t*)b+160,geometry-160)&&(!memcmp(ia,ib,pixels_a)||(getenv("NF_TEST_RACING_OWNED_CAPTURE")&&getenv("NF_TEST_MODEL_TEXTURE_TRANSITION")));}
  }
  if(ok){reason=5;memcpy(ca+pass,(uint8_t*)a+48,56);memcpy(oa+pass,(uint8_t*)a+104,56);memcpy(cb+pass,(uint8_t*)b+48,56);memcpy(ob+pass,(uint8_t*)b+104,56);NFRigidPose checked;ok=nf_pose_sample(ca+pass,cb+pass,.5,&checked)&&nf_pose_sample(oa+pass,ob+pass,.5,&checked);}
  if(!ok&&getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("model_pair_rejection older=%u newer=%u pass=%u reason=%d size_a=%llu size_b=%llu\n",older,newer,pass,reason,(unsigned long long)na,(unsigned long long)nb);
  nf_surface_free(a);nf_surface_free(b);
 }
 if(!ok)return 0;memcpy(camera_a,ca,n*sizeof(*ca));memcpy(camera_b,cb,n*sizeof(*cb));memcpy(object_a,oa,n*sizeof(*oa));memcpy(object_b,ob,n*sizeof(*ob));*count=n;return 1;
}
/* Native model vertices/UV remain source-owned; continuous pose sampling
   retains older palette until exact alpha1. Bounds must be rebuilt separately. */
API int nf_live_completed_draw_model_sample_asset(uint64_t epoch,uint32_t older,uint32_t newer,unsigned ordinal,double alpha,void**out,size_t*size){
 if(!out||!size||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFRigidPose ca[4],cb[4],oa[4],ob[4],camera,object;unsigned count=0;
 if(!nf_live_completed_draw_model_pose_pair(epoch,older,newer,ca,cb,oa,ob,4,&count)||ordinal>=count||!nf_pose_sample(ca+ordinal,cb+ordinal,alpha,&camera)||!nf_pose_sample(oa+ordinal,ob+ordinal,alpha,&object))return 0;
 void*asset=NULL;size_t bytes=0;if(!nf_live_completed_draw_model_indexed_asset(epoch,alpha==1?newer:older,ordinal,&asset,&bytes))return 0;
 /* Exact endpoints preserve original quaternion bytes and palette state. */
 if(alpha>0&&alpha<1){memcpy((uint8_t*)asset+48,&camera,56);memcpy((uint8_t*)asset+104,&object,56);}
 if(getenv("NF_TEST_FOCAL_SAMPLE")){uint32_t focals[2];if(!draw_sample_focals(epoch,older,newer,ordinal,alpha,focals)){nf_surface_free(asset);return 0;}double focal=focals[0];memcpy((uint8_t*)asset+40,&focal,8);}
 *out=asset;*size=bytes;return 1;
}
/* Rebuild model classification/portal from owned sampled Q8 position.
   Rotation is independent asset pose; command planning uses sampled Q8 xyz. */
static int draw_sample_owned_view(uint64_t epoch,uint32_t older,uint32_t newer,unsigned pass,const uint32_t a[12],const uint32_t b[12],double alpha,uint32_t out[12]){
 if(!getenv("NF_TEST_EXACT_QUERY_SAMPLE"))return nf_visibility_view_sample(a,b,alpha,out);
 unsigned x=older%16,y=newer%16;uint32_t av[12],bv[12];NFVisibilityPoseInputs pose;
 if(completed_draw_views[x].epoch!=epoch||completed_draw_views[y].epoch!=epoch||completed_draw_views[x].serial!=older||completed_draw_views[y].serial!=newer||pass>=completed_draw_views[x].count||pass>=completed_draw_views[y].count)return 0;
 if(!nf_visibility_snapshot_prepared_view(completed_draw_views[x].builders[pass],av)||!nf_visibility_snapshot_prepared_view(completed_draw_views[y].builders[pass],bv)||memcmp(a,av,48)||memcmp(b,bv,48)||!nf_visibility_snapshot_query_sample(completed_draw_views[x].builders[pass],completed_draw_views[y].builders[pass],alpha,&pose))return 0;
 memcpy(out,pose.view,48);return 1;
}
API int nf_live_completed_draw_root_model_commands_sample(uint64_t epoch,uint32_t older,uint32_t newer,unsigned ordinal,double alpha,NFNativeSceneCommand*out,unsigned capacity,unsigned*count){
 if(!out||!count||capacity<144||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFRigidPose ca[4],cb[4],oa[4],ob[4];unsigned models=0;
 if(!nf_live_completed_draw_model_pose_pair(epoch,older,newer,ca,cb,oa,ob,4,&models)||ordinal>=models){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("model_command_rejection older=%u newer=%u reason=1 models=%u\n",older,newer,models);return 0;}
 unsigned slot=(alpha==1?newer:older)%16;uint32_t address=completed_draw_views[slot].model_args[ordinal][2],views[2][12],view[12];uint8_t record[164],sampled[164];int32_t rotation[12];
 if(!nf_visibility_snapshot_read(completed_draw_views[slot].roots[ordinal],address,record,164)||!nf_visibility_snapshot_prepared_view(completed_draw_views[older%16].roots[ordinal],views[0])||!nf_visibility_snapshot_prepared_view(completed_draw_views[newer%16].roots[ordinal],views[1])||!draw_sample_owned_view(epoch,older,newer,ordinal,views[0],views[1],alpha,view))return 0;
 if(alpha>0&&alpha<1){if(!nf_object_pose_sample(record,oa+ordinal,ob+ordinal,alpha,sampled,rotation))return 0;}else memcpy(sampled,record,164);
 if(getenv("NF_TEST_FOCAL_SAMPLE")){uint32_t focals[2];if(!draw_sample_focals(epoch,older,newer,ordinal,alpha,focals))return 0;int built=nf_visibility_snapshot_prepared_builder_commands_focal(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].builders[ordinal],view,focals[0],focals[1],address,sampled,out,capacity,count);if(!built&&getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))printf("model_command_rejection older=%u newer=%u reason=2 models=%u\n",older,newer,models);return built;}
 return nf_visibility_snapshot_prepared_builder_commands_object(completed_draw_views[slot].roots[ordinal],completed_draw_views[slot].builders[ordinal],view,address,sampled,out,capacity,count);
}
/* Producer-only bounded cache; returned buffers always have separate ownership. */
static struct {uint64_t epoch;uint32_t serial;void*packet;size_t bytes;NFRigidPose cameras[144];unsigned count;} exact_scene_cache[4];
static unsigned exact_scene_cache_stats[4];
static void exact_scene_cache_clear(void){for(unsigned i=0;i<4;i++){free(exact_scene_cache[i].packet);memset(exact_scene_cache+i,0,sizeof(exact_scene_cache[i]));}}
API void nf_live_exact_scene_cache_stats(unsigned out[4]){if(out)memcpy(out,exact_scene_cache_stats,sizeof(exact_scene_cache_stats));}
/* Full exact original flip, assembled from owned native roots, never raw packets. */
static double completed_bundle_profile_mark(void){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return (double)t.QuadPart*1000/f.QuadPart;}
API int nf_live_completed_draw_scene_packet(uint64_t epoch,uint32_t serial,void**out,size_t*size,NFRigidPose*cameras,unsigned capacity,unsigned*camera_count){
 unsigned slot=serial%16;if(!out||!size||!cameras||!camera_count||capacity<144||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||!completed_draw_views[slot].count)return 0;
 int cache_enabled=getenv("NF_TEST_EXACT_SCENE_CACHE")!=NULL;unsigned cache_slot=serial%4;int cache_hit=0;
 if(cache_enabled){if(exact_scene_cache[cache_slot].epoch!=epoch||exact_scene_cache[cache_slot].serial!=serial){free(exact_scene_cache[cache_slot].packet);memset(exact_scene_cache+cache_slot,0,sizeof(exact_scene_cache[cache_slot]));}cache_hit=exact_scene_cache[cache_slot].packet!=NULL;
  if(cache_hit&&!getenv("NF_TEST_EXACT_SCENE_CACHE_VERIFY")){void*copy=malloc(exact_scene_cache[cache_slot].bytes);if(!copy)return 0;memcpy(copy,exact_scene_cache[cache_slot].packet,exact_scene_cache[cache_slot].bytes);memcpy(cameras,exact_scene_cache[cache_slot].cameras,exact_scene_cache[cache_slot].count*sizeof(*cameras));*camera_count=exact_scene_cache[cache_slot].count;*out=copy;*size=exact_scene_cache[cache_slot].bytes;exact_scene_cache_stats[0]++;return 1;}
 }
 int profile=getenv("NF_TEST_COMPLETE_CAPTURE_PROFILE")!=NULL;double commands_ms=0,model_ms=0,surface_ms=0,finish_ms=0;unsigned models_profile=0,surfaces_profile=0;
 NFSceneAssembly*assembly=nf_assembly_create();NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));uint32_t*table=malloc(131072);NFRigidPose selected[144];unsigned total=0,surfaces=0,palette_index=0;int ok=assembly&&commands&&table;
 if(ok)ok=nf_assembly_multimodel(assembly,1)&&nf_visibility_snapshot_read(completed_draw_views[slot].roots[0],0x08627700u,table,131072);
 for(unsigned pass=0;ok&&pass<completed_draw_views[slot].count;pass++){
  double command_start=profile?completed_bundle_profile_mark():0;unsigned n=0,cn=0,models=0;NFRigidPose pass_cameras[144];ok=nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&n)&&total+n<=144&&nf_live_completed_draw_root_cameras(epoch,serial,pass,pass_cameras,144,&cn)&&cn==n;if(profile)commands_ms+=completed_bundle_profile_mark()-command_start;
  for(unsigned i=0;ok&&i<n;i++){
   double asset_start=profile?completed_bundle_profile_mark():0;NFNativeSceneCommand*c=commands+i;uint32_t id[5]={c->kind==5?3:c->kind,completed_draw_views[slot].states[pass],c->source,0,0};void*asset=NULL,*light=NULL,*metadata=NULL;size_t bytes=0,light_bytes=0,metadata_bytes=0;unsigned mode=0;uint32_t unlit=0;
   if(c->kind==5){models++;memcpy(id+3,c->model+12,4);ok=models==1&&c->source==completed_draw_views[slot].model_args[pass][2]&&nf_live_completed_draw_model_indexed_asset(epoch,serial,pass,&asset,&bytes)&&nf_assembly_model(assembly,id,asset,bytes)&&nf_assembly_model_bounds(assembly,pass,c->bounds);}
   else if(c->kind==1||c->kind==2){uint32_t material_base;memcpy(&material_base,c->state+32,4);id[3]=c->kind==1?(c->xyz[2]?4:8):(c->material[0]-material_base)/32;
    ok=draw_root_asset_command(epoch,serial,pass,palette_index++,c,&asset,&bytes,&light,&light_bytes)&&draw_root_metadata_command(completed_draw_views[slot].roots[pass],c,&metadata,&metadata_bytes,&mode)&&nf_assembly_surface(assembly,id,asset,bytes,light?light:&unlit,light?light_bytes:4);
    if(ok&&getenv("NF_TEST_SURFACE_COMMAND_REUSE_VERIFY")){void*reference=NULL,*reference_light=NULL;size_t reference_bytes=0,reference_light_bytes=0;ok=nf_live_completed_draw_root_asset(epoch,serial,pass,i,&reference,&reference_bytes,&reference_light,&reference_light_bytes)&&reference_bytes==bytes&&reference_light_bytes==light_bytes&&!!reference_light==!!light&&!memcmp(reference,asset,bytes)&&(!light||!memcmp(reference_light,light,light_bytes));nf_surface_free(reference);nf_surface_free(reference_light);}
    if(ok&&getenv("NF_TEST_SURFACE_COMMAND_REUSE_VERIFY")){void*reference=NULL;size_t reference_bytes=0;unsigned reference_mode=0;ok=nf_live_completed_draw_root_metadata(epoch,serial,pass,i,&reference,&reference_bytes,&reference_mode)&&reference_bytes==metadata_bytes&&reference_mode==mode&&!memcmp(reference,metadata,metadata_bytes);free(reference);}
    if(ok&&c->kind==1){NFRoadSourceAttributes raw;size_t indices=metadata_bytes-288;memcpy(&raw,(uint8_t*)metadata+indices,288);ok=nf_assembly_surface_indices(assembly,surfaces,metadata,indices)&&nf_assembly_road_mapping(assembly,surfaces,mode==6)&&nf_assembly_road_attributes(assembly,surfaces,&raw);}
    else if(ok){if(mode==7||mode==8)ok=nf_assembly_wall_indices(assembly,surfaces,metadata,(uint8_t*)metadata+metadata_bytes/2,metadata_bytes/2,mode==8?17:1);else ok=nf_assembly_wall_states(assembly,surfaces,metadata,metadata_bytes,mode==3?17:1);}
    if(ok)ok=nf_assembly_bounds(assembly,surfaces++,0,c->bounds);
   }else ok=0;
   if(profile){double duration=completed_bundle_profile_mark()-asset_start;if(c->kind==5){model_ms+=duration;models_profile++;}else{surface_ms+=duration;surfaces_profile++;}}
   nf_surface_free(asset);nf_surface_free(light);nf_surface_free(metadata);if(ok)selected[total++]=pass_cameras[i];
  }
  if(models!=1)ok=0;
 }
 double finish_start=profile?completed_bundle_profile_mark():0;void*packet=NULL;size_t packet_size=0;if(ok)ok=nf_assembly_finish(assembly,serial,completed_draw_views[slot].begin,completed_draw_views[slot].end,completed_draw_views[slot].page,table,131072,&packet,&packet_size);
 if(profile){finish_ms=completed_bundle_profile_mark()-finish_start;printf("exact_scene_stage_profile serial=%u accepted=%d models=%u surfaces=%u commands_ms=%.6f model_ms=%.6f surface_ms=%.6f finish_ms=%.6f\n",serial,ok,models_profile,surfaces_profile,commands_ms,model_ms,surface_ms,finish_ms);}
 nf_assembly_destroy(assembly);free(commands);free(table);if(!ok)return 0;
 if(cache_enabled){if(cache_hit){if(packet_size!=exact_scene_cache[cache_slot].bytes||total!=exact_scene_cache[cache_slot].count||memcmp(packet,exact_scene_cache[cache_slot].packet,packet_size)||memcmp(selected,exact_scene_cache[cache_slot].cameras,total*sizeof(*selected))){exact_scene_cache_stats[3]++;free(packet);return 0;}exact_scene_cache_stats[2]++;}
  else if(packet_size<=16*1024*1024){void*copy=malloc(packet_size);if(copy){memcpy(copy,packet,packet_size);exact_scene_cache[cache_slot].packet=copy;exact_scene_cache[cache_slot].bytes=packet_size;exact_scene_cache[cache_slot].epoch=epoch;exact_scene_cache[cache_slot].serial=serial;exact_scene_cache[cache_slot].count=total;memcpy(exact_scene_cache[cache_slot].cameras,selected,total*sizeof(*selected));exact_scene_cache_stats[1]++;}}
 }memcpy(cameras,selected,total*sizeof(*cameras));*camera_count=total;*out=packet;*size=packet_size;return 1;
}
/* Diagnostic explicit per-pass views. Model assets retain this source scene's
   original object pose; caller must not treat this as paired object animation. */
/* NFOB v1: 64-byte header, ordered32-byte events, copy/fill offset-size
   directory, owned cameras, complete native packet, then owned2D assets.
   No pointer to bridge history survives in the returned allocation. */
API int nf_live_completed_ordered_bundle(uint64_t epoch,uint32_t serial,void**out,size_t*size){
 if(!out||!size)return 0;
 int profile=getenv("NF_TEST_COMPLETE_CAPTURE_PROFILE")!=NULL;double start=profile?completed_bundle_profile_mark():0,order_end=0,scene_end=0;
 NFOrderedSceneEvent events[608];unsigned n=0,cn=0;NFRigidPose cameras[144];void*packet=NULL;size_t packet_size=0;
 if(!nf_live_completed_operation_order(epoch,serial,events,608,&n))return 0;
 if(profile)order_end=completed_bundle_profile_mark();
 if(!nf_live_completed_draw_scene_packet(epoch,serial,&packet,&packet_size,cameras,144,&cn))return 0;
 if(profile)scene_end=completed_bundle_profile_mark();
 unsigned slot=serial%16,m=completed_indexed_copies[slot].count,geometry=0;
 for(unsigned i=0;i<n;i++)if(events[i].type>=3)geometry++;
 if(geometry!=cn||sizeof(NFOrderedSceneEvent)!=32||packet_size>16*1024*1024){free(packet);return 0;}
 size_t event_offset=64,directory_offset=event_offset+n*32,camera_offset=directory_offset+m*8,packet_offset=camera_offset+cn*sizeof(NFRigidPose),asset_offset=packet_offset+packet_size,total=asset_offset;
 for(unsigned i=0;i<m;i++)total+=completed_indexed_copies[slot].events[i].size;
 if(total>32*1024*1024){free(packet);return 0;}uint8_t*data=calloc(total,1);if(!data){free(packet);return 0;}
 uint32_t header[16]={0x424f464e,1,serial,completed_draw_views[slot].begin,completed_draw_views[slot].end,completed_draw_views[slot].page,n,m,cn,(uint32_t)event_offset,(uint32_t)directory_offset,(uint32_t)camera_offset,(uint32_t)packet_offset,(uint32_t)packet_size,(uint32_t)epoch,(uint32_t)(epoch>>32)};
 memcpy(data,header,64);memcpy(data+event_offset,events,n*32);memcpy(data+camera_offset,cameras,cn*sizeof(*cameras));memcpy(data+packet_offset,packet,packet_size);free(packet);
 for(unsigned i=0;i<m;i++){NFOwnedCopyEvent*e=completed_indexed_copies[slot].events+i;uint32_t entry[2]={(uint32_t)asset_offset,(uint32_t)e->size};memcpy(data+directory_offset+i*8,entry,8);memcpy(data+asset_offset,e->asset,e->size);asset_offset+=e->size;}
 NFOrderedBundle checked;if(!nf_ordered_bundle_view(data,total,&checked)){free(data);return 0;}
 if(profile)printf("ordered_bundle_stage_profile serial=%u events=%u cameras=%u bytes=%zu order_ms=%.6f scene_ms=%.6f pack_validate_ms=%.6f\n",serial,n,cn,total,order_end-start,scene_end-order_end,completed_bundle_profile_mark()-scene_end);*out=data;*size=total;return 1;
}
/* NFRB v1 wrapper retains the exact ordered bundle and primary road assets.
   Header8words; directory4words/asset: pass,command,offset,size. */
API int nf_live_completed_road_bundle(uint64_t epoch,uint32_t serial,void**out,size_t*size){
 if(!out||!size)return 0;void*bundle=NULL,*assets[144]={0};size_t bundle_size=0,sizes[144];unsigned event_ids[144],count=0;int ok=0;NFNativeSceneCommand*commands=NULL;unsigned command_pass=UINT32_MAX,command_count=0;
 if(!nf_live_completed_ordered_bundle(epoch,serial,&bundle,&bundle_size))return 0;
 NFOrderedBundle view;if(!nf_ordered_bundle_view(bundle,bundle_size,&view))goto done;
 for(unsigned i=0;i<view.event_count;i++){NFOrderedSceneEvent e;memcpy(&e,view.events+i*32,32);if(e.type!=3||e.kind!=1)continue;
  if(!commands){commands=malloc(144*sizeof(*commands));if(!commands)goto done;}
  if(command_pass!=e.pass){if(!nf_live_completed_draw_root_commands(epoch,serial,e.pass,commands,144,&command_count))goto done;command_pass=e.pass;}
  if(e.ordinal>=command_count)goto done;int secondary=commands[e.ordinal].xyz[2];if(secondary)continue;
  uint32_t spans[512*20];unsigned amount=0;if(!completed_road_contexts_command(serial,e.pass,commands+e.ordinal,spans,512,&amount))goto done;
  if(getenv("NF_TEST_ROAD_COMMAND_REUSE_VERIFY")){uint32_t reference[512*20];unsigned reference_count=0;if(!nf_live_completed_draw_road_contexts(epoch,serial,e.pass,e.ordinal,reference,512,&reference_count)||reference_count!=amount||memcmp(reference,spans,amount*80))goto done;}
  if(!amount)continue;
  if(count>=144||!completed_road_asset_from_contexts(serial,e.pass,e.ordinal,spans,amount,assets+count,sizes+count))goto done;event_ids[count++]=i;
 }
 void*baseline=NULL;size_t baseline_size=0;unsigned version=1;
 unsigned strip_valid=retained_strip_epoch==epoch&&retained_strip_zero[view.packet.page];
 /* Narrow current-state revalidation is fail-closed if the retained strip
    has changed. It never captures or substitutes a3D framebuffer region. */
 if(strip_valid)for(unsigned i=0;i<1920;i++)if(c->busRead8(c,0x06000000+view.packet.page*0xa000+3840+i)){strip_valid=0;break;}
 if(strip_valid){if(!nf_indexed_fill_create(0x06000000+view.packet.page*0xa000+16*240,0,1920,&baseline,&baseline_size))goto done;version=2;}
 size_t offset=32+count*16+baseline_size,total=offset+bundle_size;for(unsigned i=0;i<count;i++)total+=sizes[i];if(total>64*1024*1024){free(baseline);goto done;}
 uint8_t*data=malloc(total);if(!data){free(baseline);goto done;}uint32_t h[8]={0x4252464e,version,serial,count,32,(uint32_t)offset,(uint32_t)bundle_size,(uint32_t)total};memcpy(data,h,32);if(baseline){memcpy(data+32+count*16,baseline,baseline_size);free(baseline);}memcpy(data+offset,bundle,bundle_size);offset+=bundle_size;
 for(unsigned i=0;i<count;i++){NFOrderedSceneEvent e;memcpy(&e,view.events+event_ids[i]*32,32);uint32_t entry[4]={e.pass,e.ordinal,(uint32_t)offset,(uint32_t)sizes[i]};memcpy(data+32+i*16,entry,16);memcpy(data+offset,assets[i],sizes[i]);offset+=sizes[i];}
 NFRoadBundle checked;if(!nf_road_bundle_view(data,total,&checked)){free(data);goto done;}
 *out=data;*size=total;ok=1;
 done:for(unsigned i=0;i<count;i++)free(assets[i]);free(commands);free(bundle);return ok;
}
API int nf_live_road_bundle_validate(const void*data,size_t size){NFRoadBundle view;return nf_road_bundle_view(data,size,&view);}
API void nf_live_ordered_bundle_free(void*asset){free(asset);}
API int nf_live_completed_draw_scene_packet_views(uint64_t epoch,uint32_t serial,const uint32_t*views,unsigned view_count,void**out,size_t*size,NFRigidPose*cameras,unsigned capacity,unsigned*camera_count){
 unsigned slot=serial%16;if(!views||!out||!size||!cameras||!camera_count||capacity<144||epoch!=live_scene_epoch||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||completed_draw_views[slot].failed||!completed_draw_views[slot].count||view_count!=completed_draw_views[slot].count)return 0;
 NFSceneAssembly*assembly=nf_assembly_create();NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));uint32_t*table=malloc(131072);NFRigidPose selected[144];unsigned total=0,surfaces=0;int ok=assembly&&commands&&table;
 if(ok)ok=nf_assembly_multimodel(assembly,1)&&nf_visibility_snapshot_read(completed_draw_views[slot].roots[0],0x08627700u,table,131072);
 for(unsigned pass=0;ok&&pass<completed_draw_views[slot].count;pass++){
  unsigned n=0,models=0;NFRigidPose camera;const uint32_t*view=views+pass*12;NFPoint3 position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};ok=nf_pose_decode((const int32_t*)view,&position,&camera)&&nf_live_completed_draw_root_commands_view(epoch,serial,pass,view,commands,144,&n)&&total+n<=144;
  for(unsigned i=0;ok&&i<n;i++){
   NFNativeSceneCommand*c=commands+i;uint32_t id[5]={c->kind==5?3:c->kind,completed_draw_views[slot].states[pass],c->source,0,0};void*asset=NULL,*light=NULL,*metadata=NULL;size_t bytes=0,light_bytes=0,metadata_bytes=0;unsigned mode=0;uint32_t unlit=0;
   if(c->kind==5){models++;memcpy(id+3,c->model+12,4);ok=models==1&&c->source==completed_draw_views[slot].model_args[pass][2]&&nf_live_completed_draw_model_indexed_asset(epoch,serial,pass,&asset,&bytes)&&nf_assembly_model(assembly,id,asset,bytes)&&nf_assembly_model_bounds(assembly,pass,c->bounds);}
   else if(c->kind==1||c->kind==2){uint32_t material_base;memcpy(&material_base,c->state+32,4);id[3]=c->kind==1?(c->xyz[2]?4:8):(c->material[0]-material_base)/32;
    ok=nf_live_completed_draw_root_world_view(epoch,serial,pass,i,view,&asset,&bytes,&light,&light_bytes,&metadata,&metadata_bytes,&mode)&&nf_assembly_surface(assembly,id,asset,bytes,light?light:&unlit,light?light_bytes:4);
    if(ok&&c->kind==1){NFRoadSourceAttributes raw;size_t indices=metadata_bytes-288;memcpy(&raw,(uint8_t*)metadata+indices,288);ok=nf_assembly_surface_indices(assembly,surfaces,metadata,indices)&&nf_assembly_road_mapping(assembly,surfaces,mode==6)&&nf_assembly_road_attributes(assembly,surfaces,&raw);}
    else if(ok){if(mode==7||mode==8)ok=nf_assembly_wall_indices(assembly,surfaces,metadata,(uint8_t*)metadata+metadata_bytes/2,metadata_bytes/2,mode==8?17:1);else ok=nf_assembly_wall_states(assembly,surfaces,metadata,metadata_bytes,mode==3?17:1);}
    if(ok)ok=nf_assembly_bounds(assembly,surfaces++,0,c->bounds);
   }else ok=0;
   nf_surface_free(asset);nf_surface_free(light);nf_surface_free(metadata);if(ok)selected[total++]=camera;
  }
  if(models!=1)ok=0;
 }
 void*packet=NULL;size_t packet_size=0;if(ok)ok=nf_assembly_finish(assembly,serial,completed_draw_views[slot].begin,completed_draw_views[slot].end,completed_draw_views[slot].page,table,131072,&packet,&packet_size);
 nf_assembly_destroy(assembly);free(commands);free(table);if(!ok)return 0;
 memcpy(cameras,selected,total*sizeof(*cameras));*camera_count=total;*out=packet;*size=packet_size;return 1;
}
/* Semantic source palette resolution, never ordinal matching across changed
   visibility. Repeated source occurrences require exact palette agreement. */
static uint32_t draw_sample_bounds[9];
API void nf_live_completed_draw_sample_bounds(uint32_t out[9]){if(out)memcpy(out,draw_sample_bounds,sizeof(draw_sample_bounds));}
static uint32_t draw_sample_detail[8];
static uint32_t draw_entrant_material_audit[8];
API void nf_live_entrant_material_audit(uint32_t out[8]){if(out)memcpy(out,draw_entrant_material_audit,sizeof(draw_entrant_material_audit));}
API void nf_live_completed_draw_sample_detail(uint32_t out[8]){if(out)memcpy(out,draw_sample_detail,sizeof(draw_sample_detail));}
static const NFDrawWorldPalette*draw_transition_palette(unsigned primary,unsigned secondary,unsigned pass,const NFNativeSceneCommand*c,const uint32_t view[12],uint32_t focal){
 unsigned slots[2]={primary,secondary};const NFDrawWorldPalette*found=NULL;
 for(unsigned side=0;side<2;side++){
  unsigned slot=slots[side];if(completed_world_palettes[slot].failed||completed_world_palettes[slot].epoch!=live_scene_epoch||completed_world_palettes[slot].serial!=completed_draw_views[slot].serial){draw_sample_detail[7]=1;return NULL;}
  unsigned begin=pass?completed_draw_views[slot].timing[pass-1][5]:0,end=pass+1==completed_draw_views[slot].count?completed_world_palettes[slot].count:completed_draw_views[slot].timing[pass][5];if(begin>end||end>completed_world_palettes[slot].count){draw_sample_detail[7]=2;return NULL;}
  for(unsigned j=begin;j<end;j++){const NFDrawWorldPalette*p=completed_world_palettes[slot].draws+j;if(p->kind==c->kind&&p->source==c->source){if(found&&memcmp(found->palette,p->palette,512)){if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE")){unsigned changed=0;for(unsigned k=0;k<512;k++)changed+=found->palette[k]!=p->palette[k];printf("transition_palette_conflict primary=%u secondary=%u side=%u pass=%u kind=%u source=%u index=%u changed_bytes=%u\n",completed_draw_views[primary].serial,completed_draw_views[secondary].serial,side,pass,c->kind,c->source,j,changed);}if(getenv("NF_TEST_MOTION_CAPTURE_PROFILE")||getenv("NF_TEST_EQUIVALENT_WALL_PALETTES")){NFDrawViewReader reader={completed_draw_views[primary].roots[pass],0,view};memcpy(&reader.address,c->state+84,4);memcpy(&reader.projection,c->state+80,4);reader.focal=focal;void*assets[2]={0},*lights[2]={0};size_t sizes[2]={0},ls[2]={0};unsigned detail=0;int extracted=nf_extract_scene_command_full(c,draw_view_read,&reader,found->palette,NULL,assets,sizes,lights,ls,&detail)&&nf_extract_scene_command_full(c,draw_view_read,&reader,p->palette,NULL,assets+1,sizes+1,lights+1,ls+1,&detail);int equal=extracted&&sizes[0]==sizes[1]&&ls[0]==ls[1]&&!memcmp(assets[0],assets[1],sizes[0])&&(!ls[0]||!memcmp(lights[0],lights[1],ls[0]));unsigned index=256;for(unsigned k=0;k<256;k++)if(memcmp(found->palette+k*2,p->palette+k*2,2)){index=k;break;}printf("transition_palette_equivalence primary=%u source=%u changed_index=%u extracted=%d full_equal=%d\n",completed_draw_views[primary].serial,c->source,index,extracted,equal);if(equal&&getenv("NF_TEST_PALETTE_EQUIVALENCE_NEGATIVE")){uint8_t changed_palette[512];memcpy(changed_palette,found->palette,512);for(unsigned k=0;k<256;k++){uint16_t color;memcpy(&color,changed_palette+k*2,2);color^=0x7fff;memcpy(changed_palette+k*2,&color,2);}void*negative=NULL,*negative_light=NULL;size_t negative_size=0,negative_ls=0;int extracted_negative=nf_extract_scene_command_full(c,draw_view_read,&reader,changed_palette,NULL,&negative,&negative_size,&negative_light,&negative_ls,&detail);int rejected=extracted_negative&&(negative_size!=sizes[0]||negative_ls!=ls[0]||memcmp(negative,assets[0],sizes[0])||(ls[0]&&memcmp(negative_light,lights[0],ls[0])));printf("palette_equivalence_negative primary=%u source=%u extracted=%d rejected=%d\n",completed_draw_views[primary].serial,c->source,extracted_negative,rejected);nf_surface_free(negative);nf_surface_free(negative_light);if(!rejected)equal=0;}
nf_surface_free(assets[0]);nf_surface_free(assets[1]);nf_surface_free(lights[0]);nf_surface_free(lights[1]);if(equal&&getenv("NF_TEST_EQUIVALENT_WALL_PALETTES"))continue;}draw_sample_detail[7]=3;return NULL;}found=p;}}
  if(found){if(side){unsigned a=pass?completed_draw_views[primary].timing[pass-1][5]:0,b=pass+1==completed_draw_views[primary].count?completed_world_palettes[primary].count:completed_draw_views[primary].timing[pass][5];if(a>=b){draw_sample_detail[7]=4;return NULL;}const NFDrawWorldPalette*older=completed_world_palettes[primary].draws+a;
    for(unsigned j=a+1;j<b;j++)if(memcmp(older->palette,completed_world_palettes[primary].draws[j].palette,512)){
     /* Unused palette entries may differ. Require exact complete geometry,
        expanded material RGBA and lighting output agreement for this entrant. */
     NFDrawViewReader reader={completed_draw_views[primary].roots[pass],0,view};memcpy(&reader.address,c->state+84,4);memcpy(&reader.projection,c->state+80,4);reader.focal=focal;void*assets[2]={0},*lights[2]={0};size_t sizes[2]={0},light_sizes[2]={0};unsigned detail=0;
     int same=nf_extract_scene_command_full(c,draw_view_read,&reader,older->palette,NULL,assets,sizes,lights,light_sizes,&detail)&&nf_extract_scene_command_full(c,draw_view_read,&reader,completed_world_palettes[primary].draws[j].palette,NULL,assets+1,sizes+1,lights+1,light_sizes+1,&detail);
     int indexed_equivalent=0,indexed_policy=getenv("NF_TEST_INDEXED_ENTRANTS")&&getenv("NF_CAPTURE_WALL_OUTPUT_INDICES");
     if(getenv("NF_TEST_ENTRANT_MATERIAL_AUDIT")||indexed_policy){
      draw_entrant_material_audit[0]++;int invariant=0;
      if(same&&sizes[0]==sizes[1]&&sizes[0]>=12&&light_sizes[0]==light_sizes[1]){
       uint32_t vertices;memcpy(&vertices,assets[0],4);size_t geometry=12+(size_t)vertices*40;
       invariant=geometry<=sizes[0]&&!memcmp(assets[0],assets[1],geometry);
       if(invariant&&light_sizes[0]){uint32_t lit;memcpy(&lit,lights[0],4);size_t header=lit?20:4;invariant=light_sizes[0]>=header&&!memcmp(lights[0],lights[1],header);}
       for(size_t k=geometry+3;invariant&&k<sizes[0];k+=4)invariant=((uint8_t*)assets[0])[k]==((uint8_t*)assets[1])[k];
       for(size_t k=23;invariant&&k<light_sizes[0];k+=4)invariant=((uint8_t*)lights[0])[k]==((uint8_t*)lights[1])[k];
      }
      draw_entrant_material_audit[invariant?1:3]++;
      if(same&&sizes[0]==sizes[1]&&memcmp(assets[0],assets[1],sizes[0]))draw_entrant_material_audit[2]++;
      uint8_t*indices=NULL;uint32_t width=0,height=0,planes=1;
      int indexed=c->kind==2?nf_scene_command_wall_indices_owned(c,draw_view_read,&reader,&indices,&width,&height,&planes):nf_scene_command_road_indices_owned(c,draw_view_read,&reader,&indices,&width,&height);
      size_t pixels=(size_t)width*height;uint32_t vertices=0;if(same&&sizes[0]>=12)memcpy(&vertices,assets[0],4);size_t geometry=12+(size_t)vertices*40;
      indexed=indexed&&same&&pixels&&geometry<=sizes[0]&&sizes[0]-geometry==pixels*4&&(planes==1||planes==17);
      if(indexed&&planes==17)indexed=light_sizes[0]==20+pixels*64;
      for(unsigned bank=0;indexed&&bank<2;bank++)for(unsigned plane=0;indexed&&plane<planes;plane++){
       const uint8_t*rgba=plane?(uint8_t*)lights[bank]+20+(plane-1)*pixels*4:(uint8_t*)assets[bank]+geometry;
       const uint8_t*palette=bank?completed_world_palettes[primary].draws[j].palette:older->palette;
       for(size_t k=0;indexed&&k<pixels;k++){if(!rgba[k*4+3])continue;uint16_t color;memcpy(&color,palette+indices[plane*pixels+k]*2,2);
        for(unsigned channel=0;channel<3;channel++)if(rgba[k*4+channel]!=((color>>(channel*5))&31)*255/31)indexed=0;
        if(indexed)draw_entrant_material_audit[6]++;
       }
      }
      indexed_equivalent=invariant&&indexed;
      draw_entrant_material_audit[indexed?4:5]++;if(indexed)draw_entrant_material_audit[7]+=(uint32_t)(pixels*planes);nf_surface_free(indices);
     }
     if(same)same=sizes[0]==sizes[1]&&light_sizes[0]==light_sizes[1]&&!memcmp(assets[0],assets[1],sizes[0])&&(!light_sizes[0]||!memcmp(lights[0],lights[1],light_sizes[0]));
     if(indexed_policy&&indexed_equivalent)same=1;
     nf_surface_free(assets[0]);nf_surface_free(assets[1]);nf_surface_free(lights[0]);nf_surface_free(lights[1]);if(!same){draw_sample_detail[7]=7;return NULL;}
    }
    /* An entrant uses the established older pass palette until alpha1,
       exactly as model material state; newer source proves its identity. */
    static NFDrawWorldPalette consensus;consensus.kind=c->kind;consensus.source=c->source;memcpy(consensus.palette,older->palette,512);return &consensus;
   }return found;}
 }
 draw_sample_detail[7]=5;return NULL;
}
/* Diagnostic complete matched draw scene, sampled native world and model
   classification/assets. Topology changes reject; no draw omission. */
static int draw_scene_packet_sample_impl(uint64_t epoch,uint32_t older,uint32_t newer,double alpha,void**out,size_t*size,NFRigidPose*cameras,unsigned capacity,unsigned*camera_count,unsigned transitions){
 memset(draw_sample_detail,0,sizeof(draw_sample_detail));draw_sample_detail[0]=older;draw_sample_detail[1]=newer;draw_sample_detail[2]=1;
 if(!out||!size||!cameras||!camera_count||capacity<144||!isfinite(alpha)||alpha<0||alpha>1)return 0;
 NFRigidPose pair_a[144],pair_b[144];unsigned pair_count=0;
 if(transitions?!draw_scene_pass_pair(epoch,older,newer):!nf_live_completed_draw_camera_pair(epoch,older,newer,pair_a,pair_b,144,&pair_count))return 0;
 uint32_t serial=alpha==1?newer:older;unsigned slot=serial%16;
 draw_sample_detail[2]=2;NFSceneAssembly*assembly=nf_assembly_create();NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));uint32_t*table=malloc(131072);NFRigidPose selected[144];unsigned total=0,surfaces=0;int ok=assembly&&commands&&table;
 if(ok)ok=nf_assembly_multimodel(assembly,1)&&nf_visibility_snapshot_read(completed_draw_views[slot].roots[0],0x08627700u,table,131072);
 for(unsigned pass=0;ok&&pass<completed_draw_views[slot].count;pass++){
  draw_sample_detail[2]=3;draw_sample_detail[3]=pass;unsigned n=0,models=0;NFRigidPose camera;uint32_t source_views[2][12],sample_view[12];const uint32_t*view=sample_view;draw_sample_detail[7]=31;ok=nf_visibility_snapshot_prepared_view(completed_draw_views[older%16].roots[pass],source_views[0]);if(ok){draw_sample_detail[7]=32;ok=nf_visibility_snapshot_prepared_view(completed_draw_views[newer%16].roots[pass],source_views[1]);}if(ok){draw_sample_detail[7]=33;ok=draw_sample_owned_view(epoch,older,newer,pass,source_views[0],source_views[1],alpha,sample_view);}if(!ok)break;NFPoint3 position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};draw_sample_detail[7]=34;ok=nf_pose_decode((const int32_t*)view,&position,&camera);if(ok){draw_sample_detail[7]=35;ok=nf_live_completed_draw_root_model_commands_sample(epoch,older,newer,pass,alpha,commands,144,&n);}if(ok){draw_sample_detail[7]=36;ok=total+n<=144;}
  if(ok)draw_sample_detail[2]=4;NFNativeSceneCommand*world_commands=malloc(144*sizeof(*world_commands));unsigned wn=0;
  uint32_t sampled_focals[2]={0};if(ok&&getenv("NF_TEST_FOCAL_SAMPLE"))ok=draw_sample_focals(epoch,older,newer,pass,alpha,sampled_focals);
  if(ok)ok=world_commands&&(sampled_focals[0]?nf_live_completed_draw_root_commands_focal(epoch,serial,pass,view,sampled_focals[0],sampled_focals[1],world_commands,144,&wn):nf_live_completed_draw_root_commands_view(epoch,serial,pass,view,world_commands,144,&wn))&&wn==n;
  for(unsigned j=0;ok&&j<n;j++){NFNativeSceneCommand*a=commands+j,*b=world_commands+j;ok=a->kind==b->kind&&a->source==b->source&&a->object==b->object&&a->owner==b->owner&&a->pass==b->pass;if(ok&&(a->kind==1||a->kind==2))ok=!memcmp(a,b,sizeof(*a));}
  unsigned original_count=0;if(ok&&!transitions)ok=nf_live_completed_draw_root_commands(epoch,serial,pass,world_commands,144,&original_count)&&original_count==n;
  for(unsigned j=0;ok&&!transitions&&j<n;j++){NFNativeSceneCommand*a=commands+j,*b=world_commands+j;ok=a->kind==b->kind&&a->source==b->source&&a->object==b->object&&a->owner==b->owner&&a->pass==b->pass;}
  free(world_commands);
  for(unsigned i=0;ok&&i<n;i++){
   NFPoint3 world_position={-(double)(int32_t)view[9],-(double)(int32_t)view[10],-(double)(int32_t)view[11]};ok=nf_pose_decode((const int32_t*)view,&world_position,&camera);if(!ok)break;NFNativeSceneCommand*c=commands+i;uint32_t id[5]={c->kind==5?3:c->kind,completed_draw_views[slot].states[pass],c->source,0,0};void*asset=NULL,*light=NULL,*metadata=NULL;size_t bytes=0,light_bytes=0,metadata_bytes=0;unsigned mode=0;uint32_t unlit=0;
   draw_sample_detail[4]=i;draw_sample_detail[5]=c->kind;draw_sample_detail[6]=c->source;draw_sample_detail[7]=0;draw_sample_detail[2]=c->kind==5?6:5;
   if(c->kind==5){models++;memcpy(id+3,c->model+12,4);ok=models==1&&c->source==completed_draw_views[slot].model_args[pass][2]&&nf_live_completed_draw_model_sample_asset(epoch,older,newer,pass,alpha,&asset,&bytes)&&nf_assembly_model(assembly,id,asset,bytes)&&nf_assembly_model_bounds(assembly,pass,c->bounds);}
   else if(c->kind==1||c->kind==2){uint32_t material_base;memcpy(&material_base,c->state+32,4);id[3]=c->kind==1?(c->xyz[2]?4:8):(c->material[0]-material_base)/32;
    const NFDrawWorldPalette*resolved=transitions?draw_transition_palette(slot,(serial==older?newer:older)%16,pass,c,view,sampled_focals[0]):NULL;ok=(!transitions||resolved);if(ok){draw_sample_detail[7]=52;ok=draw_world_view_extract(slot,pass,surfaces,resolved,c,view,sampled_focals[0],&asset,&bytes,&light,&light_bytes,&metadata,&metadata_bytes,&mode);}if(ok){draw_sample_detail[7]=53;ok=nf_assembly_surface(assembly,id,asset,bytes,light?light:&unlit,light?light_bytes:4);}
    if(ok&&c->kind==1){draw_sample_detail[7]=54;NFRoadSourceAttributes raw;size_t indices=metadata_bytes-288;memcpy(&raw,(uint8_t*)metadata+indices,288);draw_sample_detail[7]=55;ok=nf_assembly_surface_indices(assembly,surfaces,metadata,indices);if(ok){draw_sample_detail[7]=56;ok=nf_assembly_road_mapping(assembly,surfaces,mode==6);}if(ok){draw_sample_detail[7]=57;ok=nf_assembly_road_attributes(assembly,surfaces,&raw);}}
    else if(ok){if(mode==7||mode==8)ok=nf_assembly_wall_indices(assembly,surfaces,metadata,(uint8_t*)metadata+metadata_bytes/2,metadata_bytes/2,mode==8?17:1);else ok=nf_assembly_wall_states(assembly,surfaces,metadata,metadata_bytes,mode==3?17:1);}
    if(ok){for(unsigned k=0;k<4;k++){draw_sample_bounds[k]=c->bounds[k];draw_sample_bounds[k+4]=(unsigned)(c->record[2+k*2]|c->record[3+k*2]<<8);}draw_sample_bounds[8]=surfaces;draw_sample_detail[7]=58;ok=nf_assembly_bounds(assembly,surfaces++,alpha==1?0:alpha,c->bounds);if(!ok&&getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))fprintf(stderr,"sample_bounds_rejection older=%u newer=%u alpha=%.17g source=%u bounds=%u,%u,%u,%u record=%u,%u,%u,%u\n",older,newer,alpha,c->source,c->bounds[0],c->bounds[1],c->bounds[2],c->bounds[3],(unsigned)(c->record[2]|c->record[3]<<8),(unsigned)(c->record[4]|c->record[5]<<8),(unsigned)(c->record[6]|c->record[7]<<8),(unsigned)(c->record[8]|c->record[9]<<8));}
   }else ok=0;
   if(ok&&c->kind==5)memcpy(&camera,(uint8_t*)asset+48,sizeof(camera));nf_surface_free(asset);nf_surface_free(light);nf_surface_free(metadata);if(ok)selected[total++]=camera;
  }
  if(ok&&models!=1){draw_sample_detail[7]=59;draw_sample_bounds[8]=models;ok=0;}
 }
 void*packet=NULL;size_t packet_size=0;if(ok)draw_sample_detail[2]=8;if(ok)ok=nf_assembly_finish(assembly,serial,completed_draw_views[slot].begin,completed_draw_views[slot].end,completed_draw_views[slot].page,table,131072,&packet,&packet_size);
 nf_assembly_destroy(assembly);free(commands);free(table);if(!ok)return 0;
 draw_sample_detail[2]=0;memcpy(cameras,selected,total*sizeof(*cameras));*camera_count=total;*out=packet;*size=packet_size;return 1;
}
API int nf_live_completed_draw_scene_packet_sample(uint64_t e,uint32_t a,uint32_t b,double alpha,void**out,size_t*size,NFRigidPose*c,unsigned cap,unsigned*n){return draw_scene_packet_sample_impl(e,a,b,alpha,out,size,c,cap,n,0);}
API int nf_live_completed_draw_scene_packet_transition(uint64_t e,uint32_t a,uint32_t b,double alpha,void**out,size_t*size,NFRigidPose*c,unsigned cap,unsigned*n){return draw_scene_packet_sample_impl(e,a,b,alpha,out,size,c,cap,n,1);}
API int nf_original_query_owned(uint64_t,uint32_t,uint32_t,uint32_t[22]);
API int nf_live_completed_builder_query(uint64_t epoch,uint32_t serial,unsigned pass,uint32_t out[14]){unsigned slot=serial%16;if(!out||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||pass>=completed_draw_views[slot].count)return 0;return nf_visibility_snapshot_owned_query(completed_draw_views[slot].builders[pass],out);}
API int nf_live_completed_builder_view(uint64_t epoch,uint32_t serial,unsigned pass,uint32_t out[12]){unsigned slot=serial%16;if(!out||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||pass>=completed_draw_views[slot].count)return 0;return nf_visibility_snapshot_prepared_view(completed_draw_views[slot].builders[pass],out);}
/* Diagnostic oracle fixture, copied from the exact completed builder owner. */
API int nf_live_completed_builder_ram(uint64_t epoch,uint32_t serial,unsigned pass,void*out,size_t size,uint32_t*state_address){unsigned slot=serial%16;if(!out||size!=0x48000||!state_address||completed_draw_views[slot].epoch!=epoch||completed_draw_views[slot].serial!=serial||pass>=completed_draw_views[slot].count)return 0;NFVisibilitySnapshot*s=completed_draw_views[slot].builders[pass];uint8_t*ram=malloc(size);if(!ram)return 0;int ok=nf_visibility_snapshot_read(s,0x02000000,ram,0x40000)&&nf_visibility_snapshot_read(s,0x03000000,ram+0x40000,0x8000);if(ok){memcpy(out,ram,size);*state_address=completed_draw_views[slot].states[pass];}free(ram);return ok;}
API int nf_live_completed_builder_query_sample(uint64_t epoch,uint32_t older,uint32_t newer,unsigned pass,double alpha,NFVisibilityPoseInputs*out){unsigned a=older%16,b=newer%16;if(completed_draw_views[a].epoch!=epoch||completed_draw_views[b].epoch!=epoch||completed_draw_views[a].serial!=older||completed_draw_views[b].serial!=newer||pass>=completed_draw_views[a].count||pass>=completed_draw_views[b].count)return 0;return nf_visibility_snapshot_query_sample(completed_draw_views[a].builders[pass],completed_draw_views[b].builders[pass],alpha,out);}
/* Per-call owned provenance; never publish the mutable global diagnostic trace. */
API int nf_live_completed_draw_occurrences_sample(uint64_t epoch,uint32_t older,uint32_t newer,unsigned pass,double alpha,uint32_t*out,unsigned capacity,unsigned*count){
 if(!out||!count||capacity<1873)return 0;NFVisibilityPoseInputs pose;uint32_t focal[2];if(!nf_live_completed_builder_query_sample(epoch,older,newer,pass,alpha,&pose)||!nf_live_completed_draw_sample_focals(epoch,older,newer,pass,alpha,focal))return 0;
 NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned n=0;int ok=nf_live_completed_draw_root_commands_focal(epoch,alpha==1?newer:older,pass,pose.view,focal[0],focal[1],commands,144,&n);uint32_t rows[1873]={0};if(ok){rows[0]=n;for(unsigned i=0;i<n;i++){NFNativeSceneCommand*c=commands+i;uint32_t*r=rows+1+i*13;r[0]=c->kind;r[1]=c->source;r[2]=c->owner;r[3]=c->pass;r[4]=c->mask;memcpy(r+5,c->record,16);for(unsigned j=0;j<4;j++)r[9+j]=c->bounds[j];}memcpy(out,rows,sizeof(rows));*count=n;}free(commands);return ok;
}
/* Producer-only staging. Constructors copy all RAM into independently owned snapshots before returning. */
static uint8_t draw_snapshot_staging_ram[0x48000];
static void draw_builder_capture(struct ARMCore*cpu,unsigned pc){
 if(!live_model_views_requested()||!draw_owned_capture_mode())return;
 if(pc==0x03004c74){nf_visibility_snapshot_destroy(draw_builder_current);draw_builder_current=NULL;draw_builder_verified=0;draw_builder_state=cpu->gprs[0];uint8_t*ram=draw_snapshot_staging_ram;
  if(ram&&native_surface_read(NULL,0x02000000,ram,0x40000)&&native_surface_read(NULL,0x03000000,ram+0x40000,0x8000))draw_builder_current=nf_visibility_snapshot_create_prepared(live_visibility.assets,ram,0x48000,draw_builder_state,rd16(0x03005d44));uint32_t owned_query[22];if(draw_builder_current&&nf_original_query_owned(live_scene_epoch,live_scene.serial,draw_builder_state,owned_query))nf_visibility_snapshot_attach_query(draw_builder_current,owned_query+6,owned_query+10);
 }else if(pc==0x03004d50&&draw_builder_current){NFVisibilityResult native,original;uint32_t queue,groups;
  int ok=nf_visibility_snapshot_evaluate(draw_builder_current,&native)&&native_surface_read(NULL,draw_builder_state,original.state,256);if(ok){memcpy(&queue,original.state+96,4);memcpy(&groups,original.state+100,4);ok=native_surface_read(NULL,queue,original.queue,NF_VISIBILITY_QUEUE_BYTES)&&native_surface_read(NULL,groups,original.groups,4096);}
  draw_builder_verified=ok&&!memcmp(&native,&original,256+NF_VISIBILITY_QUEUE_BYTES+4096);
 }
}
static void draw_view_root_capture(struct ARMCore*cpu,unsigned pc){
 if(pc!=0x03004d5c||!live_model_views_requested()||!draw_owned_capture_mode())return;
 if(!native_surface_read(NULL,0x05000000,pending_draw_views.current_root_palette,512))pending_draw_views.failed=1;
 pending_draw_views.current_root_cycles=mTimingGlobalTime(c->timing);pending_draw_views.current_root_timing[0]=c->frameCounter(c);pending_draw_views.current_root_timing[1]=c->busRead16(c,0x04000000);pending_draw_views.current_root_timing[2]=rd32(rd32(cpu->gprs[0]+80));
 nf_visibility_snapshot_destroy(pending_draw_views.current_root);pending_draw_views.current_root=NULL;uint8_t*ram=draw_snapshot_staging_ram;
 if(ram&&native_surface_read(NULL,0x02000000,ram,0x40000)&&native_surface_read(NULL,0x03000000,ram+0x40000,0x8000))pending_draw_views.current_root=nf_visibility_snapshot_create_prepared(live_visibility.assets,ram,0x48000,cpu->gprs[0],rd16(0x03005d44));
 if(!pending_draw_views.current_root)pending_draw_views.failed=1;
}
static void draw_views_publish(uint32_t serial){unsigned slot=serial%16;memcpy(completed_draw_views[slot].cycles,pending_draw_views.cycles,sizeof(pending_draw_views.cycles));memcpy(completed_draw_views[slot].timing,pending_draw_views.timing,sizeof(pending_draw_views.timing));for(unsigned i=0;i<completed_draw_views[slot].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[slot].builders[i]);memcpy(completed_draw_views[slot].builders,pending_draw_views.builders,sizeof(pending_draw_views.builders));memcpy(completed_draw_views[slot].states,pending_draw_views.states,sizeof(pending_draw_views.states));memcpy(completed_draw_views[slot].model_args,pending_draw_views.model_args,sizeof(pending_draw_views.model_args));memcpy(completed_draw_views[slot].model_inputs,pending_draw_views.model_inputs,sizeof(pending_draw_views.model_inputs));memcpy(completed_draw_views[slot].root_palettes,pending_draw_views.root_palettes,sizeof(pending_draw_views.root_palettes));memcpy(completed_world_palettes[slot].draws,pending_world_palettes.draws,sizeof(pending_world_palettes.draws));memcpy(completed_world_palettes[slot].cycles,pending_world_palettes.cycles,sizeof(pending_world_palettes.cycles));completed_world_palettes[slot].epoch=live_scene_epoch;completed_world_palettes[slot].serial=serial;completed_world_palettes[slot].count=pending_world_palettes.count;completed_world_palettes[slot].failed=pending_world_palettes.failed;for(unsigned i=0;i<completed_draw_views[slot].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[slot].views[i]);for(unsigned i=0;i<completed_draw_views[slot].count;i++)nf_visibility_snapshot_destroy(completed_draw_views[slot].roots[i]);memcpy(completed_draw_views[slot].roots,pending_draw_views.roots,sizeof(pending_draw_views.roots));memcpy(completed_draw_views[slot].views,pending_draw_views.views,sizeof(pending_draw_views.views));completed_draw_views[slot].epoch=live_scene_epoch;completed_draw_views[slot].serial=serial;completed_draw_views[slot].count=pending_draw_views.count;completed_draw_views[slot].failed=pending_draw_views.failed;nf_visibility_snapshot_destroy(pending_draw_views.current_root);memset(&pending_draw_views,0,sizeof(pending_draw_views));}
static struct {NFLiveModelInputs models[16];unsigned count,failed;} pending_model_inputs;
static struct {NFLiveModelInputs models[16];NFVisibilityIdentity id;unsigned count,valid;} completed_model_inputs[NF_COMPLETED_SURFACE_HISTORY];
static void live_model_inputs_reset(void){memset(&pending_world_palettes,0,sizeof(pending_world_palettes));draw_views_pending_clear();memset(&pending_model_inputs,0,sizeof(pending_model_inputs));}
API int nf_live_completed_models_count(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,unsigned*out){
 if(!out||epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_model_inputs[i].valid&&completed_model_inputs[i].id.epoch==epoch&&completed_model_inputs[i].id.serial==serial&&completed_model_inputs[i].id.begin_refresh==begin&&completed_model_inputs[i].id.end_refresh==end){*out=completed_model_inputs[i].count;return 1;}return 0;
}
/* Exact per-object inputs; outputs unchanged for expired/wrong identity. */
API int nf_live_completed_model_inputs_for(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t identity[5],void*out){
 unsigned count;if(!identity||!out||!nf_live_completed_models_count(epoch,serial,begin,end,&count))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_model_inputs[i].valid&&completed_model_inputs[i].id.epoch==epoch&&completed_model_inputs[i].id.serial==serial&&completed_model_inputs[i].id.begin_refresh==begin&&completed_model_inputs[i].id.end_refresh==end)for(unsigned j=0;j<count;j++)if(!memcmp(completed_model_inputs[i].models[j].identity,identity,20)){memcpy(out,completed_model_inputs[i].models[j].inputs,560);return 1;}return 0;
}
static NFLiveOwnedModel live_owned_model;
static struct {NFLiveOwnedModel model;uint64_t epoch;uint32_t serial,begin,end;unsigned valid;} completed_models[NF_COMPLETED_SURFACE_HISTORY];
static void live_owned_model_invalidate(void){nf_model_outcome_reset(&live_model_outcomes);live_model_outcome_no_draw_queries=0;indexed_copies_clear();exact_scene_cache_clear();memset(completed_world_palettes,0,sizeof(completed_world_palettes));draw_views_close();memset(completed_model_inputs,0,sizeof(completed_model_inputs));live_model_inputs_reset();live_billboard_clear();for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)completed_models[i].valid=0;live_owned_model.ready=0;live_owned_model.count=live_owned_model.used=0;live_object_model_context.verified=0;}
API void nf_live_owned_model_pending(uint32_t out[3]){if(out){out[0]=live_owned_model.ready;out[1]=live_owned_model.count;out[2]=live_owned_model.used;}}
API void nf_live_owned_model_stats(uint32_t out[4]){if(out)memcpy(out,live_owned_model.stats,16);}
static int live_owned_model_read(void*user,uint32_t address,void*out,size_t size){
 NFLiveOwnedModel*source=user?user:&live_owned_model;
 for(unsigned i=0;i<source->count;i++){
  uint32_t*b=source->blocks[i];
  if(address>=b[0]&&(uint64_t)address+size<=(uint64_t)b[0]+b[1]){memcpy(out,source->bytes+b[2]+address-b[0],size);return 1;}
 }
 return 0;
}
static void live_model_inputs_draw(void){
 unsigned n=pending_model_inputs.count;NFLiveOwnedModel*m=&live_owned_model;
 if(n>=16||!m->ready||m->epoch!=live_scene_epoch||m->args[0]!=live_scene.context||m->args[2]!=live_scene.object||m->size!=live_scene.model_size||m->hash!=surface_audit_hash(live_scene.model,live_scene.model_size)){pending_model_inputs.failed=1;return;}
 NFLiveModelInputs item;memcpy(item.identity,live_scene.identity,20);memcpy(item.inputs,m->rotation,48);item.size=m->size;item.hash=m->hash;
 if(!live_owned_model_read(m,0x05000000,item.inputs+48,512)){pending_model_inputs.failed=1;return;}
 if(live_model_views_requested()&&draw_owned_capture_mode()){
  unsigned ordinal=pending_draw_views.count;if(ordinal>=4)pending_draw_views.failed=1;else{
   uint8_t*ram=malloc(0x48000);NFVisibilitySnapshot*view=NULL;
   if(ram&&native_surface_read(NULL,0x02000000,ram,0x40000)&&native_surface_read(NULL,0x03000000,ram+0x40000,0x8000))view=nf_visibility_snapshot_create_prepared(live_visibility.assets,ram,0x48000,live_scene.state,rd16(0x03005d44));free(ram);
   if(!view)pending_draw_views.failed=1;else{pending_draw_views.cycles[ordinal][0]=pending_draw_views.current_root_cycles;pending_draw_views.cycles[ordinal][1]=mTimingGlobalTime(c->timing);pending_draw_views.timing[ordinal][0]=pending_draw_views.current_root_timing[0];pending_draw_views.timing[ordinal][1]=c->frameCounter(c);pending_draw_views.timing[ordinal][2]=pending_draw_views.current_root_timing[1];pending_draw_views.timing[ordinal][3]=c->busRead16(c,0x04000000);pending_draw_views.timing[ordinal][4]=pending_draw_views.current_root_timing[2];pending_draw_views.timing[ordinal][5]=pending_world_palettes.count;memcpy(pending_draw_views.root_palettes[ordinal],pending_draw_views.current_root_palette,512);pending_draw_views.states[ordinal]=live_scene.state;memcpy(pending_draw_views.model_args[ordinal],m->args,12);memcpy(pending_draw_views.model_inputs[ordinal],item.inputs,560);pending_draw_views.builders[ordinal]=draw_builder_verified?nf_visibility_snapshot_clone(draw_builder_current):NULL;if(!pending_draw_views.builders[ordinal])pending_draw_views.failed=1;pending_draw_views.views[ordinal]=view;pending_draw_views.roots[ordinal]=nf_visibility_snapshot_clone(pending_draw_views.current_root);if(!pending_draw_views.roots[ordinal])pending_draw_views.failed=1;pending_draw_views.count++;}
  }
 }
 pending_model_inputs.models[n]=item;pending_model_inputs.count++;
}
static uint32_t model_publish_detail[NF_COMPLETED_SURFACE_HISTORY][6];
static uint32_t model_duplicate_detail[NF_COMPLETED_SURFACE_HISTORY][8];
API int nf_live_model_duplicate_detail(uint32_t serial,uint32_t out[8]){unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;if(!out||model_duplicate_detail[slot][0]!=serial)return 0;memcpy(out,model_duplicate_detail[slot],32);return 1;}
API int nf_live_model_publish_detail(uint32_t serial,uint32_t out[6]){if(!out||model_publish_detail[serial%NF_COMPLETED_SURFACE_HISTORY][0]!=serial)return 0;memcpy(out,model_publish_detail[serial%NF_COMPLETED_SURFACE_HISTORY],24);return 1;}
static void live_model_inputs_publish(const NFScenePacket*p,const NFVisibilityIdentity*id){
 draw_views_publish(p->serial);unsigned slot=p->serial%NF_COMPLETED_SURFACE_HISTORY;completed_draw_views[slot].begin=p->begin_refresh;completed_draw_views[slot].end=p->end_refresh;completed_draw_views[slot].page=p->page;completed_model_inputs[slot].valid=0;
 unsigned count=nf_scene_packet_model_count(p),worlds;memcpy(&worlds,p->section[1].data+4,4);
 uint32_t*detail=model_publish_detail[slot];detail[0]=p->serial;detail[1]=count;detail[2]=pending_model_inputs.count;detail[3]=pending_model_inputs.failed;detail[4]=detail[5]=0;
 if(pending_model_inputs.failed||count!=pending_model_inputs.count){detail[4]=1;return;}
 for(unsigned i=0;i<count;i++){NFSceneSection model;NFLiveModelInputs*m=pending_model_inputs.models+i;
  for(unsigned j=0;j<i;j++)if(!memcmp(m->identity,pending_model_inputs.models[j].identity,20)){NFLiveModelInputs*previous=pending_model_inputs.models+j;uint32_t*duplicate=model_duplicate_detail[slot];duplicate[0]=p->serial;duplicate[1]=j;duplicate[2]=i;duplicate[3]=m->size==previous->size;duplicate[4]=m->hash==previous->hash;duplicate[5]=!memcmp(m->inputs,previous->inputs,48);duplicate[6]=!memcmp(m->inputs+48,previous->inputs+48,512);duplicate[7]=m->identity[2];detail[4]=2;detail[5]=i;return;}
  if(!nf_scene_packet_model(p,i,&model)||model.size!=m->size||surface_audit_hash(model.data,model.size)!=m->hash||memcmp(p->section[4].data+8+(worlds+i)*20,m->identity,20)){detail[4]=3;detail[5]=i;return;}
 }
 memcpy(completed_model_inputs[slot].models,pending_model_inputs.models,count*sizeof(NFLiveModelInputs));completed_model_inputs[slot].id=*id;completed_model_inputs[slot].count=count;completed_model_inputs[slot].valid=1;
}
API int nf_live_completed_model_identity(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t out[5]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_models[i].valid&&completed_models[i].epoch==epoch&&completed_models[i].serial==serial&&completed_models[i].begin==begin&&completed_models[i].end==end){
  NFLiveOwnedModel*m=&completed_models[i].model;uint32_t descriptor;
  if(m->args[0]>UINT32_MAX-12||!live_owned_model_read(m,m->args[0]+12,&descriptor,4))return 0;
  uint32_t result[5]={3,m->state,m->args[2],descriptor,0};memcpy(out,result,20);return 1;
 }
 return 0;
}
/* Owned scene input for diagnostic model regeneration. World rotation48 and
   exact model-draw palette512; never reads current emulator palette. */
API int nf_live_completed_model_inputs(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void*out){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_models[i].valid&&completed_models[i].epoch==epoch&&completed_models[i].serial==serial&&completed_models[i].begin==begin&&completed_models[i].end==end){
  NFLiveOwnedModel*m=&completed_models[i].model;uint8_t result[560];
  memcpy(result,m->rotation,48);
  if(!live_owned_model_read(m,0x05000000,result+48,512))return 0;
  memcpy(out,result,sizeof(result));return 1;
 }
 return 0;
}
typedef struct {NFDrawPalettes*bank;uint64_t epoch;uint32_t serial;const uint8_t*model_palette;unsigned failed;NFDrawPalettes*secondary;uint32_t secondary_serial;} NFLiveCommandPalette;
static uint32_t live_command_palette_missing[6];
API void nf_live_command_palette_missing(uint32_t out[6]){if(out)memcpy(out,live_command_palette_missing,24);}
static int live_command_palette_assets(void*user,unsigned ordinal,const NFNativeSceneCommand*c,NFReadMemory read,void*reader,const int32_t rotation[12],uint8_t out[512],void**asset,size_t*size,void**light,size_t*light_size){
 NFLiveCommandPalette*p=user;
 if(nf_scene_command_palette_extract(p->bank,p->epoch,p->serial,c,read,reader,rotation,out,asset,size,light,light_size))return 1;
 uint32_t first_reason[4];nf_scene_command_palette_detail(first_reason);
 if(p->secondary&&nf_scene_command_palette_extract(p->secondary,p->epoch,p->secondary_serial,c,read,reader,rotation,out,asset,size,light,light_size))return 1;
 uint32_t second_reason[4];nf_scene_command_palette_detail(second_reason);
 uint8_t colors[512];
 if(p->secondary&&first_reason[0]==1&&second_reason[0]==1&&nf_scene_command_palette_consensus_extract(p->bank,p->serial,p->secondary,p->secondary_serial,p->epoch,c,read,reader,rotation,colors,asset,size,light,light_size)){memcpy(out,colors,512);return 1;}
 uint32_t detail[6]={c->kind,c->source,c->material[0],p->serial,p->secondary_serial,ordinal};memcpy(live_command_palette_missing,detail,24);
 p->failed=1;return 0;
}
static int live_command_palette(void*user,unsigned ordinal,const NFNativeSceneCommand*c,NFReadMemory read,void*reader,const int32_t rotation[12],uint8_t out[512]){
 (void)ordinal;NFLiveCommandPalette*p=user;
 if(c->kind==5){memcpy(out,p->model_palette,512);return 1;}
 if(nf_scene_command_palette(p->bank,p->epoch,p->serial,c,read,reader,rotation,out))return 1;
 uint32_t first_reason[4];nf_scene_command_palette_detail(first_reason);
 if(p->secondary&&nf_scene_command_palette(p->secondary,p->epoch,p->secondary_serial,c,read,reader,rotation,out))return 1;
 uint32_t second_reason[4];nf_scene_command_palette_detail(second_reason);
 if(p->secondary&&first_reason[0]==1&&second_reason[0]==1&&nf_scene_command_palette_consensus(p->bank,p->serial,p->secondary,p->secondary_serial,p->epoch,c,read,reader,rotation,out))return 1;
 uint32_t detail[6]={c->kind,c->source,c->material[0],p->serial,p->secondary_serial,ordinal};memcpy(live_command_palette_missing,detail,24);
 p->failed=1;return 0;
}
/* Opt-in native packet generation from completed owned scene snapshots.
   Stage1 identity,2 retained model inputs,3 palette bank,4 producer,5 palette ambiguity/missing key. */
static int completed_native_packet_impl(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,const uint8_t*objects,unsigned object_count,NFSceneObjectCallback callback,void*callback_user,void**out,size_t*out_size,unsigned*stage,unsigned native_callbacks,const int32_t*rotation,NFDrawPalettes*secondary,uint32_t secondary_serial){
 if(stage)*stage=1;
 if(epoch!=live_scene_epoch||!pose||!out||!out_size)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];
  if(!e||e->id.epoch!=epoch||e->id.serial!=serial||e->id.begin_refresh!=begin||e->id.end_refresh!=end)continue;
  uint8_t inputs[560];if(stage)*stage=2;
  if(!nf_live_completed_model_inputs(epoch,serial,begin,end,inputs))return 0;
  if(rotation)memcpy(inputs,rotation,48);
  if(stage)*stage=3;
  NFDrawPalettes*bank=NULL;
  for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==epoch&&live_palettes.entries[j].serial==serial&&live_palettes.entries[j].begin==begin&&live_palettes.entries[j].end==end){bank=live_palettes.entries[j].bank;break;}
  if(!bank)return 0;
  NFLiveCommandPalette palettes={bank,epoch,serial,inputs+48,0,secondary,secondary_serial};
  if(stage)*stage=4;
  int ok=native_callbacks?nf_visibility_snapshot_packet_native_palettes_at(e->render_snapshot,epoch,serial,begin,end,pose,alpha,e->page,objects,object_count,(const int32_t*)inputs,live_command_palette,&palettes,out,out_size):nf_visibility_snapshot_packet_palettes_at(e->render_snapshot,epoch,serial,begin,end,pose,alpha,e->page,objects,object_count,(const int32_t*)inputs,callback,callback_user,live_command_palette,&palettes,out,out_size);
  if(!ok){if(stage&&palettes.failed)*stage=5;return 0;}
  if(stage)*stage=0;
  return 1;
 }
 return 0;
}
API int nf_live_completed_native_packet(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const NFVisibilityPoseInputs*pose,double alpha,const uint8_t*objects,unsigned object_count,NFSceneObjectCallback callback,void*callback_user,void**out,size_t*out_size,unsigned*stage){return completed_native_packet_impl(epoch,serial,begin,end,pose,alpha,objects,object_count,callback,callback_user,out,out_size,stage,0,NULL,NULL,0);}
/* Actual owned callback semantics at retained pose; no journal replay. */
API int nf_live_completed_native_packet_owned(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 NFVisibilityPoseInputs pose;if(stage)*stage=1;
 if(!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;
 return completed_native_packet_impl(epoch,serial,begin,end,&pose,0,NULL,256,NULL,NULL,out,out_size,stage,1,NULL,NULL,0);
}
API int nf_live_model_outcomes_enable(int enabled){live_model_outcomes_enabled=enabled!=0;nf_model_outcome_reset(&live_model_outcomes);live_model_outcome_no_draw_queries=0;return 1;}
API NFModelOutcome nf_live_completed_model_outcome_for(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t id[5]){
 unsigned count;if(!live_model_outcomes_enabled||!nf_live_completed_models_count(epoch,serial,begin,end,&count))return NF_MODEL_OUTCOME_UNKNOWN;
 NFModelOutcome result=nf_model_outcome_query(&live_model_outcomes,epoch,serial,begin,end,id);if(result==NF_MODEL_OUTCOME_NO_DRAW)live_model_outcome_no_draw_queries++;return result;
}
API void nf_live_model_outcome_stats(uint32_t serial,uint32_t out[4]){const NFModelOutcomeScene*s=live_model_outcomes.scenes+serial%16;if(out){out[0]=s->count;out[1]=s->failed;out[2]=s->serial;out[3]=live_model_outcome_no_draw_queries;}}
typedef struct {uint64_t epoch;uint32_t serial,begin,end;} NFLiveModelInputIdentity;
static int live_command_model_inputs(void*user,unsigned ordinal,const NFNativeSceneCommand*c,const uint32_t id[5],int32_t rotation[12],uint8_t palette[512]){
 (void)ordinal;NFLiveModelInputIdentity*identity=user;uint8_t inputs[560];
 if(c->kind!=5)return NF_MODEL_INPUT_MISSING;
 NFModelOutcome outcome=nf_live_completed_model_outcome_for(identity->epoch,identity->serial,identity->begin,identity->end,id);
 if(outcome==NF_MODEL_OUTCOME_NO_DRAW)return NF_MODEL_INPUT_OWNED_NO_DRAW;
 if(outcome==NF_MODEL_OUTCOME_CONFLICT||!nf_live_completed_model_inputs_for(identity->epoch,identity->serial,identity->begin,identity->end,id,inputs))return NF_MODEL_INPUT_MISSING;
 memcpy(rotation,inputs,48);memcpy(palette,inputs+48,512);return 1;
}
/* Diagnostic exact endpoint with every retained car; sampled paired rotations
   are still pending, so do not substitute this endpoint for moving gameplay. */
API int nf_live_completed_native_multimodel_owned(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;unsigned count;NFVisibilityPoseInputs pose;
 if(!out||!out_size||!nf_live_completed_models_count(epoch,serial,begin,end,&count)||!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  NFDrawPalettes*bank=NULL;for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==epoch&&live_palettes.entries[j].serial==serial&&live_palettes.entries[j].begin==begin&&live_palettes.entries[j].end==end)bank=live_palettes.entries[j].bank;
  if(stage)*stage=3;if(!bank)return 0;
  unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;uint8_t*inputs=completed_model_inputs[slot].models[0].inputs;
  NFLiveCommandPalette palettes={bank,epoch,serial,inputs+48,0,NULL,0};NFLiveModelInputIdentity identity={epoch,serial,begin,end};
  if(stage)*stage=4;int ok=nf_visibility_snapshot_packet_native_model_inputs_at(entry->render_snapshot,epoch,serial,begin,end,&pose,0,entry->page,NULL,256,(const int32_t*)inputs,live_command_palette,&palettes,live_command_model_inputs,&identity,out,out_size);
  if(stage)*stage=ok?0:palettes.failed?5:4;return ok;
 }return 0;
}
/* Indexed exact endpoint, not a sampled gameplay replacement. */
API int nf_live_completed_native_multimodel_indexed_owned(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;unsigned count;NFVisibilityPoseInputs pose;
 if(!out||!out_size||!nf_live_completed_models_count(epoch,serial,begin,end,&count)||!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  NFDrawPalettes*bank=NULL;for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==epoch&&live_palettes.entries[j].serial==serial&&live_palettes.entries[j].begin==begin&&live_palettes.entries[j].end==end)bank=live_palettes.entries[j].bank;
  if(stage)*stage=3;if(!bank)return 0;
  unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;uint8_t*inputs=completed_model_inputs[slot].models[0].inputs;
  NFLiveCommandPalette palettes={bank,epoch,serial,inputs+48,0,NULL,0};NFLiveModelInputIdentity identity={epoch,serial,begin,end};
  if(stage)*stage=4;int ok=nf_visibility_snapshot_packet_native_indexed_model_inputs_at(entry->render_snapshot,epoch,serial,begin,end,&pose,0,entry->page,NULL,256,(const int32_t*)inputs,live_command_palette,&palettes,live_command_model_inputs,&identity,out,out_size);
  if(stage)*stage=ok?0:palettes.failed?5:4;return ok;
 }return 0;
}
API int nf_live_completed_native_multimodel_world_indexed_owned(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;unsigned count;NFVisibilityPoseInputs pose;
 if(!out||!out_size||!nf_live_completed_models_count(epoch,serial,begin,end,&count)||!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  NFDrawPalettes*bank=NULL;for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==epoch&&live_palettes.entries[j].serial==serial&&live_palettes.entries[j].begin==begin&&live_palettes.entries[j].end==end)bank=live_palettes.entries[j].bank;
  if(stage)*stage=3;if(!bank)return 0;
  unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;uint8_t*inputs=completed_model_inputs[slot].models[0].inputs;
  NFLiveCommandPalette palettes={bank,epoch,serial,inputs+48,0,NULL,0};NFLiveModelInputIdentity identity={epoch,serial,begin,end};
  if(stage)*stage=4;int ok=nf_visibility_snapshot_packet_native_indexed_world_model_inputs_at(entry->render_snapshot,epoch,serial,begin,end,&pose,0,entry->page,NULL,256,(const int32_t*)inputs,live_command_palette,&palettes,live_command_model_inputs,&identity,out,out_size);
  if(stage)*stage=ok?0:palettes.failed?5:4;return ok;
 }return 0;
}
static int live_road_attributes_requested(void){const char*value=getenv("NF_LIVE_ROAD_ATTRIBUTES");return live_source_world_capture||(value&&value[0]=='1'&&!value[1]);}
/* Explicit source-owned capture; assets are copied by visibility enable. */
API int nf_live_source_world_capture_enable(const void*rom,size_t bytes,size_t budget){
 if(!nf_live_visibility_enable(rom,bytes,budget))return 0;
 live_source_world_capture=1;nf_visibility_snapshot_owned_callbacks(1);nf_live_surface_audit_enable(1);return 1;
}
API void nf_live_source_world_capture_disable(void){nf_live_surface_audit_enable(0);live_visibility_close();}
API int nf_live_completed_native_multimodel_world_classified_owned(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=1;unsigned count;NFVisibilityPoseInputs pose;
 if(!out||!out_size||!nf_live_completed_models_count(epoch,serial,begin,end,&count))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  uint32_t view[12];unsigned prepared=nf_visibility_snapshot_prepared_view(entry->render_snapshot,view);
  if(!prepared&&!nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose))return 0;
  NFDrawPalettes*bank=NULL;for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==epoch&&live_palettes.entries[j].serial==serial&&live_palettes.entries[j].begin==begin&&live_palettes.entries[j].end==end)bank=live_palettes.entries[j].bank;
  if(stage)*stage=3;if(!bank)return 0;
  unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;uint8_t*inputs=completed_model_inputs[slot].models[0].inputs;
  NFLiveCommandPalette palettes={bank,epoch,serial,inputs+48,0,NULL,0};NFLiveModelInputIdentity identity={epoch,serial,begin,end};
  if(stage)*stage=4;int ok=prepared?nf_visibility_snapshot_packet_prepared_assets_models(entry->render_snapshot,epoch,serial,begin,end,view,0,entry->page,NULL,256,(const int32_t*)inputs,live_command_palette_assets,&palettes,live_command_model_inputs,&identity,live_road_attributes_requested(),out,out_size):(live_road_attributes_requested()?nf_visibility_snapshot_packet_native_road_attributes_assets_model_inputs_at:nf_visibility_snapshot_packet_native_classified_assets_model_inputs_at)(entry->render_snapshot,epoch,serial,begin,end,&pose,0,entry->page,NULL,256,(const int32_t*)inputs,live_command_palette_assets,&palettes,live_command_model_inputs,&identity,out,out_size);
  if(stage)*stage=ok?0:palettes.failed?5:4;return ok;
 }return 0;
}
/* Paired presentation-only regeneration. Stable slots and one model identity;
   discrete source lists/materials/state retained from older scene until alpha1. */
API int nf_live_completed_native_pair_packet(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage){
 if(stage)*stage=10;
 if(!a||!b||!out||!out_size||!isfinite(alpha)||alpha<0||alpha>1||a->epoch!=b->epoch||a->epoch!=live_scene_epoch||a->serial>=b->serial||a->end_refresh>=b->end_refresh)return 0;
 NFCompletedSurfaceAudit*entries[2]={NULL,NULL};const NFVisibilityIdentity*ids[2]={a,b};
 for(unsigned j=0;j<2;j++)for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==ids[j]->epoch&&e->id.serial==ids[j]->serial&&e->id.begin_refresh==ids[j]->begin_refresh&&e->id.end_refresh==ids[j]->end_refresh)entries[j]=e;}
 if(!entries[0]||!entries[1])return 0;
 if(alpha==0||alpha==1){const NFVisibilityIdentity*id=alpha==0?a:b;return nf_live_completed_native_packet_owned(id->epoch,id->serial,id->begin_refresh,id->end_refresh,out,out_size,stage);}
 NFDrawPalettes*secondary=NULL;for(unsigned i=0;i<live_palettes.count;i++)if(live_palettes.entries[i].epoch==b->epoch&&live_palettes.entries[i].serial==b->serial&&live_palettes.entries[i].begin==b->begin_refresh&&live_palettes.entries[i].end==b->end_refresh)secondary=live_palettes.entries[i].bank;
 if(!secondary)return 0;
 uint32_t states[2][64],model_ids[2][5];uint8_t pools[2][256*164],sampled[256*164],inputs[2][560];NFVisibilityPoseInputs poses[2],pose;
 for(unsigned j=0;j<2;j++){
  if(!nf_live_completed_model_identity(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,model_ids[j])||!nf_visibility_snapshot_read(entries[j]->render_snapshot,model_ids[j][1],states[j],256)||!nf_visibility_snapshot_read(entries[j]->render_snapshot,states[j][15],pools[j],sizeof(pools[j]))||!nf_live_completed_visibility_pose(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,poses+j)||!nf_live_completed_model_inputs(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,inputs[j]))return 0;
 }
 if(stage)*stage=11;
 if(memcmp(model_ids[0],model_ids[1],20))return 0;
 for(unsigned j=0;j<64;j++)if((j==4||j==5||j==7||j==15||j==30||j==63)&&states[0][j]!=states[1][j])return 0;
 if(stage)*stage=12;
 if(!nf_visibility_pose_sample(poses,poses+1,alpha,&pose))return 0;
 if(stage)*stage=13;
 uint8_t mask[32]={0},reached[32];
 for(unsigned j=0;j<2;j++)for(unsigned i=0;i<entries[j]->visits[0];i++){unsigned index=entries[j]->visits[3+i*3];if(index>=256)return 0;mask[index/8]|=1u<<(index&7);}
 if(stage)*stage=14;
 NFRigidPose pa,pb;NFPoint3 origin={0};uint8_t dummy[164]={0},record[164];int32_t rotation[12];
 if(!nf_pose_decode((const int32_t*)inputs[0],&origin,&pa)||!nf_pose_decode((const int32_t*)inputs[1],&origin,&pb)||!nf_object_pose_sample(dummy,&pa,&pb,alpha,record,rotation))return 0;
 /* Seed paired slots from endpoint visits; discover missing sources with native
    traversal and expand until every visited slot
    has coherent paired data. Unreachable bytes past the actual pool stay owned. */
 for(unsigned attempt=0;attempt<=256;attempt++){
  void*packet=NULL;size_t size=0;
  if(!nf_object_pool_sample_masked(pools[0],pools[1],256,mask,alpha,sampled)){if(stage)*stage=13;return 0;}
  if(!completed_native_packet_impl(a->epoch,a->serial,a->begin_refresh,a->end_refresh,&pose,alpha,sampled,256,NULL,NULL,&packet,&size,stage,1,rotation,secondary,b->serial))return 0;
  nf_scene_command_plan_object_mask(reached);unsigned added=0;
  for(unsigned i=0;i<32;i++){added+=(reached[i]&~mask[i])!=0;mask[i]|=reached[i];}
  if(!added){*out=packet;*out_size=size;return 1;}
  nf_scene_packet_free(packet);
 }
 if(stage)*stage=15;return 0;
}
static uint32_t paired_model_inputs_missing[6];
API void nf_live_paired_model_inputs_missing(uint32_t out[6]){if(out)memcpy(out,paired_model_inputs_missing,24);}
typedef struct {const NFVisibilityIdentity*a,*b;double alpha;unsigned indexed;NFVisibilitySnapshot*older;} NFLivePairedModelInputs;
static int live_model_rotation_read(void*user,uint32_t address,void*out,size_t size){return nf_visibility_snapshot_read(user,address,out,size);}
API int nf_live_completed_object_world_rotation(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t state,uint32_t object,int32_t out[12]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;if(!completed_model_inputs[slot].valid||completed_model_inputs[slot].id.serial!=serial||state!=completed_model_inputs[slot].models[0].identity[1])return 0;
  uint32_t pool;if(state>UINT32_MAX-60u||!nf_visibility_snapshot_read(entry->render_snapshot,state+60,&pool,4)||object<pool||(uint64_t)object+164>(uint64_t)pool+256*164u||(object-pool)%164u)return 0;
  uint8_t record[164];if(!nf_visibility_snapshot_read(entry->render_snapshot,object,record,164))return 0;
  return nf_model_world_rotation_owned(live_model_rotation_read,entry->render_snapshot,record,out);
 }return 0;
}
/* Read-only diagnostic export of the original retained object record and
   original world rotation, including objects absent from visible commands. */
API int nf_live_completed_object_pose_inputs(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t state,uint32_t object,uint8_t record[164],int32_t rotation[12]){
 if(!record||!rotation)return 0;int32_t staged_rotation[12];
 if(!nf_live_completed_object_world_rotation(epoch,serial,begin,end,state,object,staged_rotation))return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];if(!entry||entry->id.epoch!=epoch||entry->id.serial!=serial||entry->id.begin_refresh!=begin||entry->id.end_refresh!=end)continue;
  uint8_t staged_record[164];if(!nf_visibility_snapshot_read(entry->render_snapshot,object,staged_record,sizeof(staged_record)))return 0;
  memcpy(record,staged_record,sizeof(staged_record));memcpy(rotation,staged_rotation,sizeof(staged_rotation));return 1;
 }return 0;
}
static int live_paired_command_model_inputs(void*user,unsigned ordinal,const NFNativeSceneCommand*c,const uint32_t id[5],int32_t rotation[12],uint8_t palette[512]){
 (void)ordinal;NFLivePairedModelInputs*p=user;uint8_t inputs[2][560],dummy[164]={0},record[164];NFPoint3 origin={0};NFRigidPose poses[2];const NFVisibilityIdentity*ids[2]={p->a,p->b};
 if(c->kind!=5)return 0;
 for(unsigned i=0;i<2;i++){if(!nf_live_completed_model_inputs_for(ids[i]->epoch,ids[i]->serial,ids[i]->begin_refresh,ids[i]->end_refresh,id,inputs[i])){
   /* Newer palette is unused before alpha1. Older missing palette may recover
      only in indexed output, with all used nonzero colors agreeing in its own
      retained banks; index0 belongs to display rows, never another car. */
   int recovered=(i==1||p->indexed)&&nf_live_completed_object_world_rotation(ids[i]->epoch,ids[i]->serial,ids[i]->begin_refresh,ids[i]->end_refresh,id[1],id[2],(int32_t*)inputs[i]);
   if(recovered&&i==0){
    uint8_t*indices=NULL;uint32_t width,height,key[3];unsigned count=0;uint8_t*colors=malloc(256*512);
    recovered=colors&&nf_model_texture_indices_owned(live_model_rotation_read,p->older,c->model,&indices,&width,&height);
    if(recovered){while(count<256&&nf_live_palette_draw(p->a->epoch,p->a->serial,p->a->begin_refresh,p->a->end_refresh,count,key,colors+count*512))count++;recovered=nf_model_display_palette(indices,(size_t)width*height,colors,count,inputs[0]+48);}
    free(indices);free(colors);
   }
   if(!recovered){paired_model_inputs_missing[0]=i+1;memcpy(paired_model_inputs_missing+1,id,20);return 0;}
  }if(!nf_pose_decode((const int32_t*)inputs[i],&origin,poses+i))return 0;}
 if(!nf_object_pose_sample(dummy,poses,poses+1,p->alpha,record,rotation))return 0;
 memcpy(palette,inputs[0]+48,512);return 1;
}
static int completed_native_multimodel_pair_impl(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage,unsigned indexed){
 if((indexed&4)&&live_road_attributes_requested())indexed|=8;
 memset(paired_model_inputs_missing,0,sizeof(paired_model_inputs_missing));
 if(stage)*stage=10;
 if(!a||!b||!out||!out_size||!isfinite(alpha)||alpha<0||alpha>1||a->epoch!=b->epoch||a->epoch!=live_scene_epoch||a->serial>=b->serial||a->end_refresh>=b->end_refresh)return 0;
 NFCompletedSurfaceAudit*entries[2]={NULL,NULL};const NFVisibilityIdentity*ids[2]={a,b};
 for(unsigned j=0;j<2;j++)for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==ids[j]->epoch&&e->id.serial==ids[j]->serial&&e->id.begin_refresh==ids[j]->begin_refresh&&e->id.end_refresh==ids[j]->end_refresh)entries[j]=e;}
 if(!entries[0]||!entries[1]){if(stage)*stage=20;return 0;}
 if(alpha==0||alpha==1){const NFVisibilityIdentity*id=alpha==0?a:b;return ((indexed&4)?nf_live_completed_native_multimodel_world_classified_owned:(indexed&2)?nf_live_completed_native_multimodel_world_indexed_owned:indexed?nf_live_completed_native_multimodel_indexed_owned:nf_live_completed_native_multimodel_owned)(id->epoch,id->serial,id->begin_refresh,id->end_refresh,out,out_size,stage);}
 NFDrawPalettes*secondary=NULL;for(unsigned i=0;i<live_palettes.count;i++)if(live_palettes.entries[i].epoch==b->epoch&&live_palettes.entries[i].serial==b->serial&&live_palettes.entries[i].begin==b->begin_refresh&&live_palettes.entries[i].end==b->end_refresh)secondary=live_palettes.entries[i].bank;
 if(!secondary)return 0;
 uint32_t states[2][64],model_ids[2][5];uint8_t pools[2][256*164],sampled[256*164],inputs[2][560];NFVisibilityPoseInputs poses[2],pose;uint32_t prepared_views[2][12],sampled_view[12];unsigned prepared[2];
 for(unsigned j=0;j<2;j++)prepared[j]=nf_visibility_snapshot_prepared_view(entries[j]->render_snapshot,prepared_views[j]);
 if(prepared[0]!=prepared[1]||(prepared[0]&&!(indexed&4)))return 0;
 for(unsigned j=0;j<2;j++){
  unsigned model_count;if(!nf_live_completed_models_count(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,&model_count)){if(stage)*stage=17;return 0;}memcpy(model_ids[j],completed_model_inputs[ids[j]->serial%NF_COMPLETED_SURFACE_HISTORY].models[0].identity,20);
  if(!nf_visibility_snapshot_read(entries[j]->render_snapshot,model_ids[j][1],states[j],256)||!nf_visibility_snapshot_read(entries[j]->render_snapshot,states[j][15],pools[j],sizeof(pools[j]))||(!prepared[j]&&!nf_live_completed_visibility_pose(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,poses+j))||!nf_live_completed_model_inputs_for(ids[j]->epoch,ids[j]->serial,ids[j]->begin_refresh,ids[j]->end_refresh,model_ids[j],inputs[j]))return 0;
 }
 if(stage)*stage=11;
 if(model_ids[0][1]!=model_ids[1][1])return 0;
 for(unsigned j=0;j<64;j++)if((j==4||j==5||j==7||j==15||j==30||j==63)&&states[0][j]!=states[1][j])return 0;
 if(stage)*stage=12;
 if(prepared[0]){if(!nf_visibility_view_sample(prepared_views[0],prepared_views[1],alpha,sampled_view))return 0;}else if(!nf_visibility_pose_sample(poses,poses+1,alpha,&pose))return 0;
 if(stage)*stage=13;
 uint8_t mask[32]={0},reached[32];
 for(unsigned j=0;j<2;j++)for(unsigned i=0;i<entries[j]->visits[0];i++){unsigned index=entries[j]->visits[3+i*3];if(index>=256)return 0;mask[index/8]|=1u<<(index&7);}
 if(stage)*stage=14;
 NFRigidPose pa,pb;NFPoint3 origin={0};uint8_t dummy[164]={0},record[164];int32_t rotation[12];
 if(!nf_pose_decode((const int32_t*)inputs[0],&origin,&pa)||!nf_pose_decode((const int32_t*)inputs[1],&origin,&pb)||!nf_object_pose_sample(dummy,&pa,&pb,alpha,record,rotation))return 0;
 /* Seed paired slots from endpoint visits; discover missing sources with native
    traversal and expand until every visited slot
    has coherent paired data. Unreachable bytes past the actual pool stay owned. */
 for(unsigned attempt=0;attempt<=256;attempt++){
  void*packet=NULL;size_t size=0;
  if(!nf_object_pool_sample_masked(pools[0],pools[1],256,mask,alpha,sampled)){if(stage)*stage=13;return 0;}
  NFDrawPalettes*bank=NULL;for(unsigned j=0;j<live_palettes.count;j++)if(live_palettes.entries[j].epoch==a->epoch&&live_palettes.entries[j].serial==a->serial&&live_palettes.entries[j].begin==a->begin_refresh&&live_palettes.entries[j].end==a->end_refresh)bank=live_palettes.entries[j].bank;if(!bank)return 0;
  NFLiveCommandPalette palettes={bank,a->epoch,a->serial,inputs[0]+48,0,secondary,b->serial};NFLivePairedModelInputs models={a,b,alpha,indexed,entries[0]->render_snapshot};
  int produced=prepared[0]?nf_visibility_snapshot_packet_prepared_assets_models(entries[0]->render_snapshot,a->epoch,a->serial,a->begin_refresh,a->end_refresh,sampled_view,alpha,entries[0]->page,sampled,256,rotation,live_command_palette_assets,&palettes,live_paired_command_model_inputs,&models,(indexed&8)!=0,&packet,&size):(indexed&4)?((indexed&8)?nf_visibility_snapshot_packet_native_road_attributes_assets_model_inputs_at:nf_visibility_snapshot_packet_native_classified_assets_model_inputs_at)(entries[0]->render_snapshot,a->epoch,a->serial,a->begin_refresh,a->end_refresh,&pose,alpha,entries[0]->page,sampled,256,rotation,live_command_palette_assets,&palettes,live_paired_command_model_inputs,&models,&packet,&size):((indexed&4)?nf_visibility_snapshot_packet_native_classified_world_model_inputs_at:(indexed&2)?nf_visibility_snapshot_packet_native_indexed_world_model_inputs_at:indexed?nf_visibility_snapshot_packet_native_indexed_model_inputs_at:nf_visibility_snapshot_packet_native_model_inputs_at)(entries[0]->render_snapshot,a->epoch,a->serial,a->begin_refresh,a->end_refresh,&pose,alpha,entries[0]->page,sampled,256,rotation,live_command_palette,&palettes,live_paired_command_model_inputs,&models,&packet,&size);
  if(!produced){if(stage)*stage=paired_model_inputs_missing[0]?16:palettes.failed?5:4;return 0;}
  nf_scene_command_plan_object_mask(reached);unsigned added=0;
  for(unsigned i=0;i<32;i++){added+=(reached[i]&~mask[i])!=0;mask[i]|=reached[i];}
  if(!added){if(stage)*stage=0;*out=packet;*out_size=size;return 1;}
  nf_scene_packet_free(packet);
 }
 if(stage)*stage=15;return 0;
}
API int nf_live_completed_native_multimodel_pair_packet(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage){return completed_native_multimodel_pair_impl(a,b,alpha,out,out_size,stage,0);}
API int nf_live_completed_native_multimodel_indexed_pair_packet(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage){return completed_native_multimodel_pair_impl(a,b,alpha,out,out_size,stage,1);}
static uint32_t completed_callback_detail[4];
static uint8_t completed_callback_bits[64];
API void nf_live_completed_callback_replay_bits(uint8_t out[64]){if(out)memcpy(out,completed_callback_bits,64);}
API void nf_live_completed_callback_replay_detail(uint32_t out[4]){if(out)memcpy(out,completed_callback_detail,16);}
typedef struct {NFCompletedSurfaceAudit*entry;unsigned used,failed,changed;} NFCompletedCallbackReplay;
static int completed_callback_replay(void*user,unsigned index,unsigned selector,uint8_t*objects,unsigned count,uint8_t bits[32],uint32_t matrix[12],uint32_t*head,uint32_t*maximum){
 NFCompletedCallbackReplay*p=user;if(p->used>=p->entry->callback_count){p->failed=1;return 0;}
 const NFObjectReplayCallback*r=p->entry->callbacks+p->used;
 unsigned mismatch=(r->index!=index?1:0)|(r->selector!=selector?2:0)|(memcmp(bits,r->before_bits,32)?4:0)|(memcmp(matrix,r->before_matrix,48)?8:0)|(*head!=r->before_head?16:0)|(*maximum!=r->before_maximum?32:0)|(r->count>256?64:0);
 if(mismatch){if(mismatch&4){memcpy(completed_callback_bits,bits,32);memcpy(completed_callback_bits+32,r->before_bits,32);}p->failed=mismatch;return 0;}
 for(unsigned i=0;i<r->count;i++)if(r->changes[i].offset>=count*164u||objects[r->changes[i].offset]!=r->changes[i].before){p->failed=1;return 0;}
 for(unsigned i=0;i<r->count;i++)objects[r->changes[i].offset]=r->changes[i].after;
 memcpy(bits,r->bits,32);memcpy(matrix,r->matrix,48);*head=r->head;*maximum=r->maximum;p->changed+=r->count;p->used++;return 1;
}
/* Retained endpoint replay only. Sampled poses need actual native callback semantics. */
API int nf_live_completed_native_packet_replay(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*out_size,unsigned*stage){
 memset(completed_callback_detail,0,16);memset(completed_callback_bits,0,64);if(stage)*stage=1;if(epoch!=live_scene_epoch||!out||!out_size)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(!e||e->id.epoch!=epoch||e->id.serial!=serial||e->id.begin_refresh!=begin||e->id.end_refresh!=end)continue;
  if(stage)*stage=6;if(e->callback_failed)return 0;
  NFVisibilityPoseInputs pose;if(!nf_visibility_snapshot_pose(e->snapshot,epoch,serial,begin,end,&pose))return 0;
  NFCompletedCallbackReplay replay={e,0,0,0};void*packet=NULL;size_t size=0;
  int ok=nf_live_completed_native_packet(epoch,serial,begin,end,&pose,0,NULL,256,completed_callback_replay,&replay,&packet,&size,stage);
  completed_callback_detail[0]=replay.failed;completed_callback_detail[1]=replay.used;completed_callback_detail[2]=e->callback_count;completed_callback_detail[3]=replay.changed;
  if(!ok||replay.failed||replay.used!=e->callback_count){nf_scene_packet_free(packet);if(stage&&replay.failed)*stage=8;return 0;}
  *out=packet;*out_size=size;if(stage)*stage=0;return 1;
 }
 return 0;
}
API int nf_live_completed_object_visits(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t out[1+2048*3]){
 if(!out||epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(e&&e->id.epoch==epoch&&e->id.serial==serial&&e->id.begin_refresh==begin&&e->id.end_refresh==end){memcpy(out,e->visits,sizeof(e->visits));return 1;}}
 return 0;
}
API int nf_live_completed_callback_journal(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,uint32_t out[3]){
 if(epoch!=live_scene_epoch||!out)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*e=completed_surface_audit[i];if(!e||e->id.epoch!=epoch||e->id.serial!=serial||e->id.begin_refresh!=begin||e->id.end_refresh!=end)continue;
  uint32_t result[3]={e->callback_count,e->callback_failed,0};for(unsigned j=0;j<e->callback_count;j++)result[2]+=e->callbacks[j].count;memcpy(out,result,12);return 1;
 }
 return 0;
}
API int nf_live_completed_model_verify(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end){
 if(epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_models[i].valid&&completed_models[i].epoch==epoch&&completed_models[i].serial==serial&&completed_models[i].begin==begin&&completed_models[i].end==end){
  NFLiveOwnedModel*m=&completed_models[i].model;void*data=NULL;size_t size=0;
  int ok=nf_extract_model(live_owned_model_read,m,m->args[0],m->args[1],m->args[2],m->rotation,&data,&size);
  int exact=ok&&size==m->size&&surface_audit_hash(data,size)==m->hash;nf_surface_free(data);return exact;
 }
 return 0;
}

API int nf_live_completed_model_extract(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*bytes){
 if(!out||!bytes||epoch!=live_scene_epoch)return 0;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_models[i].valid&&completed_models[i].epoch==epoch&&completed_models[i].serial==serial&&completed_models[i].begin==begin&&completed_models[i].end==end){
  NFLiveOwnedModel*m=&completed_models[i].model;void*data=NULL;size_t size=0;
  int ok=nf_extract_model(live_owned_model_read,m,m->args[0],m->args[1],m->args[2],m->rotation,&data,&size);
  if(!ok||size!=m->size||surface_audit_hash(data,size)!=m->hash){nf_surface_free(data);return 0;}
  *out=data;*bytes=size;return 1;
 }
 return 0;
}
static void live_owned_model_verify(void){
 if(!live_owned_model.ready)return;
 if(live_owned_model.epoch!=live_scene_epoch){live_owned_model_invalidate();return;}
 live_owned_model.ready=0;live_owned_model.stats[0]++;void*model=NULL;size_t size=0;
 int ok=nf_extract_model(live_owned_model_read,NULL,live_owned_model.args[0],live_owned_model.args[1],live_owned_model.args[2],live_owned_model.rotation,&model,&size);
 if(ok&&size==live_owned_model.size&&surface_audit_hash(model,size)==live_owned_model.hash)live_owned_model.stats[1]++;else live_owned_model.stats[2]++;
 nf_surface_free(model);
}
API int nf_live_owned_model_flush(uint64_t epoch){
 if(epoch!=live_scene_epoch)return -1;
 if(!live_owned_model.ready)return 0;
 if(live_owned_model.epoch!=epoch){live_owned_model_invalidate();return -1;}
 unsigned prior=live_owned_model.stats[1];live_owned_model_verify();return live_owned_model.stats[1]==prior+1?1:-1;
}
static int live_model_audit_read(void*user,uint32_t address,void*out,size_t size){
 (void)user;uint32_t base=live_object_model_context.address;
 int ok;
 if(address>=base&&(uint64_t)address+size<=(uint64_t)base+68){memcpy(out,live_object_model_context.context+(address-base),size);ok=1;}else ok=native_surface_read(NULL,address,out,size);
 if(!ok)return 0;
 if(live_owned_model.count>=128||size>sizeof(live_owned_model.bytes)-live_owned_model.used){live_owned_model.stats[3]++;return 0;}
 uint32_t*block=live_owned_model.blocks[live_owned_model.count++];block[0]=address;block[1]=(uint32_t)size;block[2]=live_owned_model.used;
 memcpy(live_owned_model.bytes+live_owned_model.used,out,size);live_owned_model.used+=(uint32_t)size;
 live_model_reads.reads++;live_model_reads.bytes+=size;
 unsigned i=0;for(;i<live_model_reads.count;i++)if(live_model_reads.ranges[i][0]==address&&live_model_reads.ranges[i][1]==size)break;
 if(i==live_model_reads.count){if(i==128){live_model_reads.overflow++;return 1;}live_model_reads.count++;live_model_reads.ranges[i][0]=address;live_model_reads.ranges[i][1]=(uint32_t)size;}
 live_model_reads.ranges[i][2]++;return 1;
}
static int validated_model_audit_read(void*user,uint32_t address,void*out,size_t size){
 int*exact=user;if(!live_model_audit_read(NULL,address,out,size)){*exact=0;return 0;}
 size_t needed=size?size:1;
 if(needed>surface_audit_scratch_capacity){uint8_t*grown=realloc(surface_audit_scratch,needed);if(!grown){*exact=0;return 1;}surface_audit_scratch=grown;surface_audit_scratch_capacity=needed;surface_audit_scratch_stats[1]++;surface_audit_scratch_stats[2]=needed;}
 if(!nf_memory_read_matches(native_surface_read,NULL,address,out,size,surface_audit_scratch,surface_audit_scratch_capacity))*exact=0;
 return 1;
}
static int live_native_context_read(void*user,uint32_t address,void*out,size_t size){
 (void)user;uint32_t base=live_object_model_context.address;
 if(address>=base&&(uint64_t)address+size<=(uint64_t)base+68){memcpy(out,live_object_model_context.context+(address-base),size);return 1;}
 return native_surface_read(NULL,address,out,size);
}

#include "../model_context_refresh.inc"
static int live_native_context_matches(unsigned context,unsigned object,uint64_t epoch,unsigned serial,unsigned frame){
 return live_object_model_context.verified&&live_object_model_context.address==context&&live_object_model_context.object==object&&live_object_model_context.epoch==epoch&&live_object_model_context.serial==serial&&live_object_model_context.frame==frame;
}
static uint32_t live_native_context_guard_stats[2];
API void nf_live_native_context_guard_stats(uint32_t out[2]){if(out)memcpy(out,live_native_context_guard_stats,8);}
static uint32_t live_native_model_assembly_stats[3],live_owned_model_assembly_stats[2];
API void nf_live_owned_model_assembly_stats(uint32_t out[2]){if(out)memcpy(out,live_owned_model_assembly_stats,8);}
API void nf_live_native_model_assembly_stats(uint32_t out[3]){if(out)memcpy(out,live_native_model_assembly_stats,12);}
static int live_native_model_assemble(unsigned context,unsigned camera,unsigned object,const int32_t*rotation,void**model,size_t*size){
 if(!live_surface_audit.enabled)return nf_extract_model(native_surface_read,NULL,context,camera,object,rotation,model,size);
 live_native_model_assembly_stats[0]++;
 if(!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c))){nf_context_rejection_capture(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c));live_native_model_assembly_stats[2]++;return 0;}
 unsigned frame=c->frameCounter(c);
 int rejected[5]={!live_native_context_matches(context^4u,object,live_scene_epoch,live_scene.serial,frame),!live_native_context_matches(context,object^4u,live_scene_epoch,live_scene.serial,frame),!live_native_context_matches(context,object,live_scene_epoch^1ull,live_scene.serial,frame),!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial^1u,frame),!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,frame^1u)};
 for(unsigned i=0;i<5;i++)live_native_context_guard_stats[rejected[i]?0:1]++;
 live_object_model_context.verified=0;
 live_native_context_guard_stats[!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,frame)?0:1]++;
 if(!live_owned_model.ready||live_owned_model.epoch!=live_scene_epoch||live_owned_model.args[0]!=context||live_owned_model.args[1]!=camera||live_owned_model.args[2]!=object||memcmp(live_owned_model.rotation,rotation,48)){live_owned_model_assembly_stats[1]++;live_native_model_assembly_stats[2]++;return 0;}
 int ok=nf_extract_model(live_owned_model_read,NULL,context,camera,object,rotation,model,size);
 live_owned_model_assembly_stats[ok?0:1]++;
 live_native_model_assembly_stats[ok?1:2]++;return ok;
}
static void live_native_context_extract_event(struct ARMCore*cpu,unsigned pc){
 if(!live_surface_audit.enabled||pc!=0x030045e0)return;
 live_owned_model_verify();live_owned_model.count=live_owned_model.used=0;
 live_native_context_extract_stats[0]++;
 if((unsigned)cpu->gprs[0]!=live_object_model_context.address||!live_object_model_context.expected){live_native_context_extract_stats[3]++;return;}
 unsigned slot=rd32(cpu->gprs[0]+60),frame=c->frameCounter(c);
 for(unsigned i=0;i<16;i++)if(live_scene.rotations[i].address==slot&&live_scene.rotations[i].frame>=live_scene.begin&&live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){
  void*original=NULL,*native=NULL;size_t original_size=0,native_size=0;
  int exact=1;
  int b=nf_extract_model(validated_model_audit_read,&exact,cpu->gprs[0],live_scene.camera,live_scene.object,live_scene.rotations[i].matrix,&native,&native_size);
  int a;
  if(b&&exact&&!model_validation_force_full){a=1;original=native;original_size=native_size;model_validation_stats[0]++;}
  else {model_validation_stats[1]++;a=nf_extract_model(native_surface_read,NULL,cpu->gprs[0],live_scene.camera,live_scene.object,live_scene.rotations[i].matrix,&original,&original_size);}
  if(a&&b&&original_size==native_size&&!memcmp(original,native,original_size)){live_native_context_extract_stats[1]++;
#ifdef NF_MODEL_CONTEXT_REFRESH_HANDOFF
 nf_context_refresh_commit(cpu->gprs[0],live_scene.object,live_scene_epoch,live_scene.serial,frame);
#endif
 }else live_native_context_extract_stats[2]++;
  if(b){live_owned_model.state=live_scene.state;live_owned_model.args[0]=cpu->gprs[0];live_owned_model.args[1]=live_scene.camera;live_owned_model.args[2]=live_scene.object;memcpy(live_owned_model.rotation,live_scene.rotations[i].matrix,48);live_owned_model.size=native_size;live_owned_model.hash=surface_audit_hash(native,native_size);live_owned_model.epoch=live_scene_epoch;live_owned_model.ready=1;}
  if(original!=native)nf_surface_free(original);nf_surface_free(native);return;
 }
 live_native_context_extract_stats[3]++;
}
static __attribute__((noinline)) void live_visibility_event_detail(struct ARMCore*cpu,unsigned pc){
 draw_builder_capture(cpu,pc);draw_view_root_capture(cpu,pc);
 if(live_surface_audit.enabled&&live_visibility.stage==3){
  if(pc==0x03004d5c){unsigned state=live_visibility.state;
   uint8_t*ram=malloc(0x48000);nf_visibility_snapshot_destroy(render_snapshot_pending);render_snapshot_pending=NULL;
   if(ram&&native_surface_read(NULL,0x02000000,ram,0x40000)&&native_surface_read(NULL,0x03000000,ram+0x40000,0x8000))render_snapshot_pending=live_visibility.prepared?nf_visibility_snapshot_create_prepared(live_visibility.assets,ram,0x48000,state,live_visibility.selected):nf_visibility_snapshot_create(live_visibility.assets,ram,0x48000,state,live_visibility.selected,live_visibility.recovery,live_visibility.base,live_visibility.query,live_visibility.view);
   free(ram);

  /* Compare query-time ownership against original root-dispatch list inputs. */
  snapshot_root_coherence[0]++;
  uint8_t retained_heads[1024],current_heads[1024],retained_objects[256*164],current_objects[256*164];
  uint32_t heads_address=rd32(state+12),objects_address=rd32(state+60);
  if(!nf_visibility_snapshot_read(live_visibility.pending,heads_address,retained_heads,sizeof(retained_heads))||!native_surface_read(NULL,heads_address,current_heads,sizeof(current_heads))||!nf_visibility_snapshot_read(live_visibility.pending,objects_address,retained_objects,sizeof(retained_objects))||!native_surface_read(NULL,objects_address,current_objects,sizeof(current_objects)))snapshot_root_coherence[4]++;
  else {
   for(unsigned i=0;i<512;i++)if(memcmp(retained_heads+i*2,current_heads+i*2,2))snapshot_root_coherence[1]++;
   for(unsigned i=0;i<256;i++){if(memcmp(retained_objects+i*164+2,current_objects+i*164+2,2))snapshot_root_coherence[2]++;if(memcmp(retained_objects+i*164+0x48,current_objects+i*164+0x48,2))snapshot_root_coherence[3]++;}
  }

  }
  if(pc==0x03002020&&region_invocations.depth){unsigned n=scene_object_visits[0],r=region_invocations.stack[region_invocations.depth-1];if(n<2048){scene_object_visits[1+n*3]=region_invocations.records[r][0]&65535;scene_object_visits[2+n*3]=region_invocations.records[r][5];scene_object_visits[3+n*3]=cpu->gprs[1];scene_object_visits[0]++;}}

  if(pc==0x030027f0){
   if(region_invocations.count>=256||region_invocations.depth>=64)region_invocations.failed++;
   else {unsigned i=region_invocations.count++;uint32_t*r=region_invocations.records[i];
    if(!native_surface_read(NULL,cpu->gprs[1],r,16))region_invocations.failed++;
    r[4]=cpu->gprs[14];r[5]=cpu->gprs[2];r[6]=deferred_surface_audit.count+deferred_surface_audit.model_count;r[7]=UINT32_MAX;r[8]=region_invocations.depth;
    region_invocations.stack[region_invocations.depth++]=i;
   }
  }else if(pc==0x03002b68){
   if(!region_invocations.depth)region_invocations.failed++;
   else region_invocations.records[region_invocations.stack[--region_invocations.depth]][7]=deferred_surface_audit.count+deferred_surface_audit.model_count;
  }
 }
 if(pc==0x030027f0&&live_surface_audit.enabled&&(unsigned)cpu->gprs[14]==0x03002364){
  NFObjectInvocation item;item.address=cpu->gprs[7];item.state_address=cpu->gprs[0];item.record_address=cpu->gprs[1];
  if(object_invocations.count>=64||!native_surface_read(NULL,item.address,item.object,164)||!native_surface_read(NULL,item.state_address,item.state,256)||!native_surface_read(NULL,item.record_address,item.record,16)||!native_surface_read(NULL,0x05000000,object_invocations.palettes[object_invocations.count],512))object_invocations.failed++;
  else {unsigned index=object_invocations.count++;object_invocations.items[index]=item;object_invocations.slots[index]=deferred_surface_audit.count+deferred_surface_audit.model_count;}
 }
 if(pc==0x030027f0&&live_surface_audit.enabled){region_object_address=0;memset(region_object_capture,0,164);if((unsigned)cpu->gprs[14]==0x03002364&&native_surface_read(NULL,cpu->gprs[7],region_object_capture,164))region_object_address=cpu->gprs[7];region_origin[6]=cpu->gprs[14];region_origin[7]=cpu->gprs[13];for(unsigned i=0;i<4;i++)region_origin[8+i]=cpu->gprs[i];}


 if(pc==0x03004770&&live_surface_audit.enabled&&live_scene.started&&cpu->gprs[0]==1&&live_scene.model&&(unsigned)cpu->gprs[4]==live_scene.context){live_model_inputs_draw();if(live_visibility.stage==3){deferred_surface_audit.model_slot=deferred_surface_audit.count;deferred_surface_audit.model_count++;}}
 live_billboard_event(cpu,pc);
 if(!live_visibility.history||!live_scene.started)return;
 live_object_cursor_event(cpu,pc);
 live_object_collector_event(cpu,pc);
 live_object_draw_setup_event(cpu,pc);
 live_object_visible_event(cpu,pc);
 live_object_material_event(cpu,pc);
 live_object_texture_event(cpu,pc);
 live_object_model_context_event(cpu,pc);
 live_native_context_extract_event(cpu,pc);
 live_object_visit_event(cpu,pc);
 live_object_insert_event(cpu,pc);
 live_object_sort_event(cpu,pc);
 live_object_distance_event(cpu,pc);
 live_region_link_event(cpu,pc);
 live_region_geometry_event(cpu,pc);
 live_wall_plan_event(cpu,pc);
 if(live_visibility.stage==3&&(pc==0x03000304||pc==0x030032f0)){
  live_visibility_check_palette(1);
  if(live_surface_audit.enabled){
   uint64_t audit_started=capture_profile_enabled?capture_profile_now():0,hash_ticks=0;
   void*surface=NULL,*lighting=NULL;size_t bytes=0,light_bytes=0;int ok;
   NFRetainedSurfaceAudit retained={0};retained.snapshot=live_visibility.pending;retained.state_address=cpu->gprs[1];retained.material_address=cpu->gprs[0];
   int inputs_ok=native_surface_read(NULL,retained.state_address,retained.state,256)&&native_surface_read(NULL,retained.material_address,retained.material,48)&&native_surface_read(NULL,0x05000000,retained.palette,512);
   NFValidatedSurfaceRead validation={&retained,inputs_ok,getenv("NF_TEST_SURFACE_READ_REUSE")!=NULL,getenv("NF_VERIFY_SURFACE_READ_REUSE")!=NULL};
   if(pc==0x03000304)ok=nf_extract_wall(validated_surface_audit_read,&validation,cpu->gprs[1],live_scene.world_descriptor,cpu->gprs[6],cpu->gprs[0],cpu->gprs[3],cpu->gprs[2],&surface,&bytes,&lighting,&light_bytes);
   else ok=nf_extract_road_layer(validated_surface_audit_read,&validation,cpu->gprs[1],cpu->gprs[7],cpu->gprs[0],cpu->gprs[2],rd32(cpu->gprs[13]+4),&surface,&bytes);
   uint64_t audit_extracted=capture_profile_enabled?capture_profile_now():0;if(capture_profile_enabled)surface_capture_profile_ticks[0]+=audit_extracted-audit_started;
   if(ok)live_surface_audit.stats[4]++;
   live_surface_audit.retained_stats[0]++;
   if(inputs_ok){
    void*copy=NULL,*copy_light=NULL;size_t copy_bytes=0,copy_light_bytes=0;int copied;
    /* Deterministic extraction: equality of every consumed input implies the
       same surface/light output. Otherwise keep the complete differential. */
    if(ok&&validation.exact&&!surface_validation_force_full){copied=1;copy=surface;copy_light=lighting;copy_bytes=bytes;copy_light_bytes=light_bytes;surface_validation_stats[0]++;}
    else {surface_validation_stats[1]++;
     if(pc==0x03000304)copied=nf_extract_wall(retained_surface_audit_read,&retained,cpu->gprs[1],live_scene.world_descriptor,cpu->gprs[6],cpu->gprs[0],cpu->gprs[3],cpu->gprs[2],&copy,&copy_bytes,&copy_light,&copy_light_bytes);
     else copied=nf_extract_road_layer(retained_surface_audit_read,&retained,cpu->gprs[1],cpu->gprs[7],cpu->gprs[0],cpu->gprs[2],rd32(cpu->gprs[13]+4),&copy,&copy_bytes);
    }
    if(!copied)live_surface_audit.retained_stats[2]++;
    else if(!ok||copy_bytes!=bytes||copy_light_bytes!=light_bytes||memcmp(copy,surface,bytes)||(light_bytes&&memcmp(copy_light,lighting,light_bytes)))live_surface_audit.retained_stats[3]++;
    else {
     live_surface_audit.retained_stats[1]++;
     if(deferred_surface_audit.count==256)deferred_surface_audit.stats[3]++;
     else {
      NFDeferredSurfaceAudit*d=&deferred_surface_audit.draws[deferred_surface_audit.count++];d->inputs=retained;d->wall=pc==0x03000304;memcpy(d->origin,region_origin,48);d->object_address=region_object_address;memcpy(d->region_object,region_object_capture,164);memcpy(d->wall_pass,captured_wall_pass,12);
      d->args[0]=cpu->gprs[1];d->args[1]=d->wall?live_scene.world_descriptor:(unsigned)cpu->gprs[7];d->args[2]=cpu->gprs[6];d->args[3]=cpu->gprs[0];d->args[4]=d->wall?(unsigned)cpu->gprs[3]:(unsigned)cpu->gprs[2];d->args[5]=d->wall?(unsigned)cpu->gprs[2]:rd32(cpu->gprs[13]+4);
      d->bytes=bytes;d->light_bytes=light_bytes;if(capture_profile_enabled){surface_capture_profile_bytes[d->wall?1:0]+=bytes;surface_capture_profile_bytes[2]+=light_bytes;}uint64_t hash_started=capture_profile_enabled?capture_profile_now():0;d->hash=surface_audit_hash(surface,bytes);d->light_hash=surface_audit_hash(lighting,light_bytes);if(capture_profile_enabled){hash_ticks=capture_profile_now()-hash_started;surface_capture_profile_ticks[2]+=hash_ticks;}
     }
    }
    if(copy!=surface)nf_surface_free(copy);if(copy_light!=lighting)nf_surface_free(copy_light);
   }else live_surface_audit.retained_stats[2]++;
   nf_surface_free(surface);nf_surface_free(lighting);
   if(capture_profile_enabled){surface_capture_profile_ticks[1]+=capture_profile_now()-audit_extracted-hash_ticks;surface_capture_profile_ticks[3]++;}
  }
  if(live_palettes.pending){uint8_t colors[512];unsigned wall=pc==0x03000304;
   if(!native_surface_read(NULL,0x05000000,colors,512)||!nf_draw_palettes_append(live_palettes.pending,wall?2:1,cpu->gprs[wall?6:7],wall?(unsigned)cpu->gprs[3]:rd32(cpu->gprs[0]+40),colors,512)){
    nf_draw_palettes_destroy(live_palettes.pending);live_palettes.pending=NULL;live_palettes.stats[2]++;
   }else live_palettes.stats[0]++;
  }
 }
 if(pc==0x03004c74&&live_visibility.stage!=1&&live_visibility.history&&rd32(0x03005f14)==1){
  unsigned frontend=c->busRead8(c,0x03006710),handler=rd32(0x08653ae0+frontend*4);
  if((frontend==13&&handler==0x08011f1d)||(frontend==1&&handler==0x08011415)){
   live_visibility_reset();live_visibility.prepared=1;live_visibility.stats[0]++;live_visibility.state=cpu->gprs[0];live_visibility.epoch=live_scene_epoch;live_visibility.serial=live_scene.serial;live_visibility.query_frame=c->frameCounter(c);live_visibility.selected=rd16(0x03005d44);
   if(!native_surface_read(NULL,0x02000000,live_visibility.ram,0x40000)||!native_surface_read(NULL,0x03000000,live_visibility.ram+0x40000,0x8000)){live_visibility.stats[2]++;return;}
   live_visibility.pending=nf_visibility_snapshot_create_prepared(live_visibility.assets,live_visibility.ram,sizeof(live_visibility.ram),live_visibility.state,live_visibility.selected);
   if(!live_visibility.pending||!nf_visibility_snapshot_prepared_view(live_visibility.pending,live_visibility.view)){live_visibility_reset();live_visibility.stats[2]++;return;}
   live_visibility.stage=2;return;
  }
 }
 if(pc==0x08002cb4){
  live_visibility_reset();live_visibility.stats[0]++;live_visibility.state=cpu->gprs[10];
  live_visibility.epoch=live_scene_epoch;live_visibility.serial=live_scene.serial;live_visibility.query_frame=c->frameCounter(c);
  live_visibility.selected=rd16(0x03005d44);live_visibility.base[0]=cpu->gprs[1];live_visibility.base[1]=cpu->gprs[0];
  unsigned sp=cpu->gprs[13];live_visibility.recovery=rd16(rd32(sp+0xa4)+0x78);
  if(!native_surface_read(NULL,rd32(sp+0x98),live_visibility.query,48)||!native_surface_read(NULL,0x02000000,live_visibility.ram,0x40000)||!native_surface_read(NULL,0x03000000,live_visibility.ram+0x40000,0x8000)){live_visibility.stats[2]++;return;}
  live_visibility.stage=1;
 }else if(pc==0x03004c74&&live_visibility.stage==1){
  if(live_visibility.epoch!=live_scene_epoch||live_visibility.serial!=live_scene.serial||live_visibility.state!=(unsigned)cpu->gprs[0]){live_visibility_reset();live_visibility.stats[2]++;return;}
  if(!native_surface_read(NULL,rd32(live_visibility.state+0x54),live_visibility.view,48)){live_visibility_reset();live_visibility.stats[2]++;return;}
  live_visibility.pending=nf_visibility_snapshot_create(live_visibility.assets,live_visibility.ram,sizeof(live_visibility.ram),live_visibility.state,live_visibility.selected,live_visibility.recovery,live_visibility.base,live_visibility.query,live_visibility.view);
  if(!live_visibility.pending){live_visibility_reset();live_visibility.stats[2]++;return;}
  live_visibility.stage=2;
 }else if(pc==0x03004d50&&live_visibility.stage==2){
  NFVisibilityResult native,original;unsigned state=live_visibility.state;
  /* Compare query-time ownership against original builder-end list inputs. */
  snapshot_object_coherence[0]++;
  uint8_t retained_heads[1024],current_heads[1024],retained_objects[256*164],current_objects[256*164];
  uint32_t heads_address=rd32(state+12),objects_address=rd32(state+60);
  if(!nf_visibility_snapshot_read(live_visibility.pending,heads_address,retained_heads,sizeof(retained_heads))||!native_surface_read(NULL,heads_address,current_heads,sizeof(current_heads))||!nf_visibility_snapshot_read(live_visibility.pending,objects_address,retained_objects,sizeof(retained_objects))||!native_surface_read(NULL,objects_address,current_objects,sizeof(current_objects)))snapshot_object_coherence[4]++;
  else {
   for(unsigned i=0;i<512;i++)if(memcmp(retained_heads+i*2,current_heads+i*2,2))snapshot_object_coherence[1]++;
   for(unsigned i=0;i<256;i++){if(memcmp(retained_objects+i*164+2,current_objects+i*164+2,2))snapshot_object_coherence[2]++;if(memcmp(retained_objects+i*164+0x48,current_objects+i*164+0x48,2))snapshot_object_coherence[3]++;}
  }

  int ok=nf_visibility_snapshot_evaluate(live_visibility.pending,&native)&&native_surface_read(NULL,state,original.state,256)&&native_surface_read(NULL,rd32(state+0x60),original.queue,NF_VISIBILITY_QUEUE_BYTES)&&native_surface_read(NULL,rd32(state+0x64),original.groups,4096);
  original.selected=rd16(0x03005d44);
  if(!ok||memcmp(&native,&original,sizeof(native))){live_visibility_reset();live_visibility.stats[2]++;return;}
  live_palettes.pending=nf_draw_palettes_create(live_visibility.epoch,live_visibility.serial);
  if(!live_palettes.pending)live_palettes.stats[2]++;
  live_visibility.palette_valid=native_surface_read(NULL,0x05000000,live_visibility.palette,512);
  if(live_visibility.palette_valid)live_visibility.palette_stats[0]++;
  live_visibility.builder_frame=c->frameCounter(c);live_visibility.stats[1]++;live_visibility.stage=3;
 }
}
/* Entire captured scene regenerated from owned histories, no packet sections. */
API int nf_live_completed_scene_extract(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,void**out,size_t*size){
 if(epoch!=live_scene_epoch||!out||!size)return 0;
 NFCompletedSurfaceAudit*entry=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++)if(completed_surface_audit[i]&&completed_surface_audit[i]->id.epoch==epoch&&completed_surface_audit[i]->id.serial==serial&&completed_surface_audit[i]->id.begin_refresh==begin&&completed_surface_audit[i]->id.end_refresh==end)entry=completed_surface_audit[i];
 if(!entry||entry->model_count!=1||entry->model_slot>entry->count)return 0;
 NFSceneAssembly*assembly=nf_assembly_create();uint32_t*table=malloc(32768*4);int ok=assembly&&table;
 if(ok)ok=nf_visibility_snapshot_read(entry->snapshot,0x08627700,table,32768*4);
 for(unsigned i=0;ok&&i<=entry->count;i++){
  uint32_t id[5];void*data=NULL,*light=NULL;size_t bytes=0,light_bytes=0;
  if(i==entry->model_slot){
   ok=nf_live_completed_model_identity(epoch,serial,begin,end,id)&&nf_live_completed_model_extract(epoch,serial,begin,end,&data,&bytes);
   if(ok)ok=nf_assembly_model(assembly,id,data,bytes);
   nf_surface_free(data);data=NULL;
  }
  if(ok&&i<entry->count){
   ok=nf_live_completed_surface_identity(epoch,serial,begin,end,i,id)&&nf_live_completed_surface_extract(epoch,serial,begin,end,i,&data,&bytes,&light,&light_bytes);
   uint32_t unlit=0;if(ok)ok=nf_assembly_surface(assembly,id,data,bytes,light_bytes?light:&unlit,light_bytes?light_bytes:4);
   nf_surface_free(data);nf_surface_free(light);
  }
 }
 if(ok)ok=nf_assembly_finish(assembly,serial,begin,end,entry->page,table,32768*4,out,size);
 nf_assembly_destroy(assembly);free(table);return ok;
}
API void nf_live_lifecycle_visibility_hooks(uint32_t out[12]){if(out)memcpy(out,lifecycle_visibility_hooks,sizeof(lifecycle_visibility_hooks));}
static uint32_t original_query_history[16][22];
API int nf_original_query_owned(uint64_t epoch,uint32_t serial,uint32_t state,uint32_t out[22]){uint32_t*r=original_query_history[serial%16];if(!out||!r[0]||!r[9]||r[1]!=(uint32_t)epoch||r[2]!=(uint32_t)(epoch>>32)||r[3]!=serial||r[5]!=state)return 0;memcpy(out,r,22*4);return 1;}
static uint32_t original_query_trace[22];
API void nf_original_query_trace(uint32_t out[22]){if(out)memcpy(out,original_query_trace,sizeof(original_query_trace));}
static void live_visibility_event(struct ARMCore*cpu,unsigned pc){
 if(pc==0x08002cb4){original_query_trace[0]++;original_query_trace[1]=(uint32_t)live_scene_epoch;original_query_trace[2]=(uint32_t)(live_scene_epoch>>32);original_query_trace[3]=live_scene.serial;original_query_trace[4]=c->frameCounter(c);original_query_trace[5]=cpu->gprs[10];original_query_trace[6]=cpu->gprs[1];original_query_trace[7]=cpu->gprs[0];original_query_trace[8]=rd16(0x03005d44);uint32_t sp=cpu->gprs[13];original_query_trace[9]=native_surface_read(NULL,rd32(sp+0x98),original_query_trace+10,48);memcpy(original_query_history[live_scene.serial%16],original_query_trace,sizeof(original_query_trace));}
 if(pc==0x0806c098){lifecycle_visibility_hooks[8]=cpu->gprs[14];lifecycle_visibility_hooks[9]=cpu->gprs[0];lifecycle_visibility_hooks[10]=cpu->gprs[1];lifecycle_visibility_hooks[11]=cpu->gprs[2];}if(pc==0x08002cb4)lifecycle_visibility_hooks[0]++;if(pc==0x03004c74){lifecycle_visibility_hooks[1]++;if(lifecycle_visibility_hooks[1]==1){native_surface_read(NULL,0x02000000,lifecycle_builder_ram,0x40000);native_surface_read(NULL,0x03000000,lifecycle_builder_ram+0x40000,0x8000);memcpy(lifecycle_builder_registers,cpu->gprs,64);}lifecycle_visibility_hooks[3]=cpu->gprs[0];lifecycle_visibility_hooks[4]=cpu->gprs[1];lifecycle_visibility_hooks[5]=cpu->gprs[13];lifecycle_visibility_hooks[6]=cpu->gprs[14];lifecycle_visibility_hooks[7]=live_visibility.stage;}if(pc==0x03004d50){lifecycle_visibility_hooks[2]++;if(lifecycle_visibility_hooks[2]==1){native_surface_read(NULL,0x02000000,lifecycle_builder_end_ram,0x40000);native_surface_read(NULL,0x03000000,lifecycle_builder_end_ram+0x40000,0x8000);}}
 /* Dispatch only observed event addresses; keep in sync with event handlers. */
 switch(pc){
 case 0x03000304:case 0x03001800:case 0x03001ff4:case 0x03002000:case 0x03002020:case 0x03002088:case 0x03002090:case 0x0300209c:case 0x030020f0:case 0x030020f8:case 0x030021f8:case 0x03002204:case 0x03002284:case 0x03002320:case 0x03002368:case 0x030023b8:case 0x03002410:case 0x03002460:case 0x03002578:case 0x03002588:case 0x03002628:case 0x0300262c:case 0x0300264c:case 0x030027e4:case 0x030027f0:case 0x03002b68:case 0x030032f0:case 0x030045e0:case 0x03004770:case 0x03004c74:case 0x03004d5c:case 0x03004d50:case 0x08002cb4:break;
 default:return;
 }
 uint64_t started=capture_profile_enabled?capture_profile_now():0;
 live_visibility_event_detail(cpu,pc);
 if(capture_profile_enabled){uint64_t ticks=capture_profile_now()-started;capture_profile_ticks[0]+=ticks;capture_profile_ticks[1]++;capture_profile_event(pc,ticks);}
}

static void live_visibility_packet(const void*data,size_t size){
 if(!live_visibility.history||live_visibility.stage!=3)return;
 NFScenePacket packet;
 if(!nf_scene_packet_view(data,size,&packet)||live_visibility.epoch!=live_scene_epoch||live_visibility.serial!=packet.serial){live_visibility_reset();live_visibility.stats[2]++;return;}
 /* Copy ownership closes at the original page flip, before this callback. */
 for(unsigned i=0;i<deferred_surface_audit.count;i++){
  NFDeferredSurfaceAudit*d=&deferred_surface_audit.draws[i];void*surface=NULL,*light=NULL;size_t bytes=0,light_bytes=0;int ok;deferred_surface_audit.stats[0]++;
  if(d->wall)ok=nf_extract_wall(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[2],d->args[3],d->args[4],d->args[5],&surface,&bytes,&light,&light_bytes);
  else ok=nf_extract_road_layer(retained_surface_audit_read,&d->inputs,d->args[0],d->args[1],d->args[3],d->args[4],d->args[5],&surface,&bytes);
  if(ok&&bytes==d->bytes&&light_bytes==d->light_bytes&&surface_audit_hash(surface,bytes)==d->hash&&surface_audit_hash(light,light_bytes)==d->light_hash)deferred_surface_audit.stats[1]++;
  else deferred_surface_audit.stats[2]++;
  nf_surface_free(surface);nf_surface_free(light);
 }
 NFVisibilityIdentity identity={live_scene_epoch,packet.serial,packet.begin_refresh,packet.end_refresh,live_visibility.query_frame,live_visibility.builder_frame};
 live_model_inputs_publish(&packet,&identity);
 live_visibility_check_palette(0);
 if(live_visibility.palette_valid&&nf_visibility_snapshot_set_palette(live_visibility.pending,live_visibility.palette,512))live_visibility.palette_stats[3]++;
 if(live_surface_audit.enabled&&live_owned_model.ready&&live_owned_model.epoch==live_scene_epoch&&packet.section[0].size==live_owned_model.size&&surface_audit_hash(packet.section[0].data,packet.section[0].size)==live_owned_model.hash){
  unsigned slot=packet.serial%NF_COMPLETED_SURFACE_HISTORY;completed_models[slot].model=live_owned_model;completed_models[slot].epoch=live_scene_epoch;completed_models[slot].serial=packet.serial;completed_models[slot].begin=packet.begin_refresh;completed_models[slot].end=packet.end_refresh;completed_models[slot].valid=1;
 }
 if(live_surface_audit.enabled&&deferred_surface_audit.count){
  NFCompletedSurfaceAudit*entry=malloc(sizeof(*entry));
  if(entry){entry->render_snapshot=nf_visibility_snapshot_clone(render_snapshot_pending);entry->snapshot=nf_visibility_snapshot_clone(live_visibility.pending);
   if(!entry->snapshot||!entry->render_snapshot||!nf_visibility_snapshot_bind(entry->snapshot,&identity)||!nf_visibility_snapshot_bind(entry->render_snapshot,&identity)){nf_visibility_snapshot_destroy(entry->render_snapshot);nf_visibility_snapshot_destroy(entry->snapshot);free(entry);}
   else {memcpy(entry->visits,scene_object_visits,sizeof(scene_object_visits));entry->callback_count=scene_callback_journal.count;entry->callback_failed=scene_callback_journal.failed;memcpy(entry->callbacks,scene_callback_journal.records,entry->callback_count*sizeof(entry->callbacks[0]));entry->region_count=region_invocations.count;entry->region_failed=region_invocations.failed+region_invocations.depth;memcpy(entry->regions,region_invocations.records,region_invocations.count*36);memcpy(entry->object_palettes,object_invocations.palettes,object_invocations.count*512);memcpy(entry->object_slots,object_invocations.slots,object_invocations.count*sizeof(uint32_t));entry->object_count=object_invocations.count;entry->object_failed=object_invocations.failed;memcpy(entry->objects,object_invocations.items,object_invocations.count*sizeof(object_invocations.items[0]));entry->id=identity;entry->page=packet.page;entry->count=deferred_surface_audit.count;entry->model_slot=deferred_surface_audit.model_slot;entry->model_count=deferred_surface_audit.model_count;memcpy(entry->draws,deferred_surface_audit.draws,entry->count*sizeof(entry->draws[0]));
    for(unsigned i=0;i<entry->count;i++)entry->draws[i].inputs.snapshot=entry->snapshot;
    if(completed_surface_audit[0]){nf_visibility_snapshot_destroy(completed_surface_audit[0]->render_snapshot);nf_visibility_snapshot_destroy(completed_surface_audit[0]->snapshot);free(completed_surface_audit[0]);}
    for(unsigned i=1;i<NF_COMPLETED_SURFACE_HISTORY;i++)completed_surface_audit[i-1]=completed_surface_audit[i];completed_surface_audit[NF_COMPLETED_SURFACE_HISTORY-1]=entry;
   }
  }
 }
 if(nf_visibility_snapshot_bind(live_visibility.pending,&identity)&&nf_visibility_history_push(live_visibility.history,live_visibility.pending))live_visibility.stats[3]++;
 else live_visibility.stats[2]++;
 if(live_palettes.pending&&nf_draw_palettes_seal(live_palettes.pending)){
  if(live_palettes.count==16){nf_draw_palettes_destroy(live_palettes.entries[0].bank);memmove(live_palettes.entries,live_palettes.entries+1,15*sizeof(live_palettes.entries[0]));live_palettes.count--;live_palettes.stats[3]++;}
  unsigned i=live_palettes.count++;live_palettes.entries[i].bank=live_palettes.pending;live_palettes.entries[i].epoch=identity.epoch;live_palettes.entries[i].serial=identity.serial;live_palettes.entries[i].begin=identity.begin_refresh;live_palettes.entries[i].end=identity.end_refresh;
  live_palettes.pending=NULL;live_palettes.stats[1]++;
 }
 live_visibility_reset();
}




API int nf_live_completed_native_multimodel_world_indexed_pair_packet(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage){return completed_native_multimodel_pair_impl(a,b,alpha,out,out_size,stage,3);}

API int nf_live_completed_native_multimodel_world_classified_pair_packet(const NFVisibilityIdentity*a,const NFVisibilityIdentity*b,double alpha,void**out,size_t*out_size,unsigned*stage){return completed_native_multimodel_pair_impl(a,b,alpha,out,out_size,stage,7);}





/* Additive candidate: copy sky metadata and complete owned source bytes. */
API int nf_live_completed_sky_read(uint64_t epoch,uint32_t serial,unsigned ordinal,void*out,size_t capacity,size_t*required){
 unsigned slot=serial%16;
 if(!required||epoch!=live_scene_epoch||completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].failed)return 0;
 NFOwnedCopyEvent*event=NULL;unsigned found=0;
 for(unsigned i=0;i<completed_indexed_copies[slot].count;i++)if(completed_indexed_copies[slot].events[i].sky[0]){if(found++==ordinal)event=completed_indexed_copies[slot].events+i;}
 if(!event||event->size!=40+15136)return 0;
 *required=56+15136;if(!out)return capacity==0;if(capacity<*required)return 0;
 uint32_t source;memcpy(&source,(uint8_t*)event->asset+8,4);
 uint32_t h[14]={0x4b53464e,1,(uint32_t)epoch,(uint32_t)(epoch>>32),event->refresh,event->sky[1],event->sky[2],event->sky[3],source,event->sky[5],event->sky[6],15136,event->sky[4],0};
 memcpy(out,h,56);memcpy((uint8_t*)out+56,(uint8_t*)event->asset+40,15136);return 1;
}

API int nf_live_completed_sky_identity(uint64_t epoch,uint32_t serial,uint32_t*out){
 unsigned slot=serial%16;
 if(!out||epoch!=live_scene_epoch||completed_indexed_copies[slot].epoch!=epoch||completed_indexed_copies[slot].serial!=serial||completed_indexed_copies[slot].failed)return 0;
 out[0]=serial;out[1]=completed_indexed_copies[slot].begin;out[2]=completed_indexed_copies[slot].end;return 1;
}

API int nf_live_completed_sky_publication_identity(uint64_t epoch,uint32_t refresh,uint32_t*out){
 if(!out||!refresh||epoch!=live_scene_epoch)return 0;
 unsigned found=0,slot=0;
 for(unsigned i=0;i<16;i++)if(completed_indexed_copies[i].epoch==epoch&&!completed_indexed_copies[i].failed&&completed_indexed_copies[i].end==refresh-1){found++;slot=i;}
 if(found!=1)return 0;
 uint32_t id[3]={completed_indexed_copies[slot].serial,completed_indexed_copies[slot].begin,completed_indexed_copies[slot].end};memcpy(out,id,12);return 1;
}

