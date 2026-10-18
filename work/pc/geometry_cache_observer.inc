/* Optional exact-endpoint memoization. The completed render snapshots own RAM
 * and ROM inputs and are read-only after publication. Their live entry and
 * pointers are revalidated before EVERY lookup. Mutable model/outcome state is
 * copied canonically into the guard. Returned packets remain independently owned.
 * Generation diagnostics (e.g. no-draw query counts) count actual regeneration,
 * not cache hits. No emulated step or source publication happens here. */
#include "geometry_packet_cache.h"
static NFGeometryCache android_geometry_cache;
static unsigned android_geometry_cache_initialized, android_geometry_cache_enabled;
static DWORD android_geometry_cache_thread;
static uint64_t android_geometry_cache_epoch, android_geometry_cache_bypasses;
typedef struct {
 uintptr_t entry, render_snapshot, query_snapshot, assets, bank;
 uint32_t prepared, view[12], road_attributes, count, outcomes_enabled;
 NFVisibilityPoseInputs pose;
 struct {uint32_t identity[5];uint8_t inputs[560];size_t size;uint64_t hash;} models[16];
 NFModelOutcomeScene outcome;
 unsigned bank_draws, bank_palettes;size_t bank_bytes;
 uint32_t bank_first_key[3];
} NFGeometryProducerGuard;
_Static_assert(sizeof(NFGeometryProducerGuard)<=NF_GEOMETRY_CACHE_MAX_GUARD,"producer guard capacity");

void nf_android_geometry_cache_reset(int disable){
 if(android_geometry_cache_initialized)nf_geometry_cache_clear(&android_geometry_cache);
 android_geometry_cache_epoch=0;
 if(disable)android_geometry_cache_enabled=0;
}
int nf_android_geometry_cache_enable(int enabled){
 if(!c||!android_source_world)return 0;
 if(android_geometry_cache_enabled&&GetCurrentThreadId()!=android_geometry_cache_thread)return 0;
 if(!android_geometry_cache_initialized){
  /* 32 MiB resident target leaves staging room within the hard 64 MiB cap. */
  if(!nf_geometry_cache_init(&android_geometry_cache,32u*1024u*1024u))return 0;
  android_geometry_cache_initialized=1;
 }
 nf_android_geometry_cache_reset(0);
 android_geometry_cache_enabled=enabled!=0;android_geometry_cache_thread=GetCurrentThreadId();return 1;
}
int nf_android_geometry_cache_info(uint64_t out[12]){
 if(!out)return 0;
 if(android_geometry_cache_enabled&&GetCurrentThreadId()!=android_geometry_cache_thread)return 0;
 NFGeometryCache*x=&android_geometry_cache;
 uint64_t values[12]={android_geometry_cache_enabled,x->hits,x->misses,x->stores,x->evictions,x->clears,x->used,x->peak,x->budget,x->allocation_failures,android_geometry_cache_bypasses,0};
 for(unsigned i=0;i<NF_GEOMETRY_CACHE_SLOTS;i++)values[11]+=x->entries[i].valid;
 memcpy(out,values,sizeof(values));return 1;
}
static int android_geometry_guard(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,NFGeometryCacheKey*key,NFGeometryProducerGuard*g){
 unsigned count,slot=serial%NF_COMPLETED_SURFACE_HISTORY;
 if(getenv("NF_TRACE_NATIVE_COMMANDS")||getenv("NF_TEST_MOTION_CAPTURE_PROFILE"))return 0;
 if(!c||!android_source_world||epoch!=nf_native_scene_epoch()||begin>end||
    !nf_live_completed_models_count(epoch,serial,begin,end,&count)||!count||count>16)return 0;
 /* The producer uses this exact modulo slot for its first-model rotation. */
 const NFVisibilityIdentity*id=&completed_model_inputs[slot].id;
 if(!completed_model_inputs[slot].valid||completed_model_inputs[slot].count!=count||
    id->epoch!=epoch||id->serial!=serial||id->begin_refresh!=begin||id->end_refresh!=end)return 0;
 NFCompletedSurfaceAudit*e=NULL;
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*p=completed_surface_audit[i];
  if(p&&p->id.epoch==epoch&&p->id.serial==serial&&p->id.begin_refresh==begin&&p->id.end_refresh==end){e=p;break;}
 }
 if(!e||!e->render_snapshot||!live_visibility.assets)return 0;
 NFDrawPalettes*bank=NULL;
 for(unsigned i=0;i<live_palettes.count;i++)if(live_palettes.entries[i].epoch==epoch&&live_palettes.entries[i].serial==serial&&live_palettes.entries[i].begin==begin&&live_palettes.entries[i].end==end)bank=live_palettes.entries[i].bank;
 memset(g,0,sizeof(*g));
 /* A successful key read requires a sealed bank. Empty banks bypass caching. */
 if(!bank||!nf_draw_palettes_info(bank,&g->bank_draws,&g->bank_palettes,&g->bank_bytes)||!nf_draw_palettes_key(bank,0,g->bank_first_key))return 0;
 g->entry=(uintptr_t)e;g->render_snapshot=(uintptr_t)e->render_snapshot;g->query_snapshot=(uintptr_t)e->snapshot;g->assets=(uintptr_t)live_visibility.assets;g->bank=(uintptr_t)bank;
 g->prepared=nf_visibility_snapshot_prepared_view(e->render_snapshot,g->view);
 if(!g->prepared&&!nf_live_completed_visibility_pose(epoch,serial,begin,end,&g->pose))return 0;
 g->road_attributes=live_road_attributes_requested();g->count=count;
 for(unsigned i=0;i<count;i++){
  NFLiveModelInputs*m=completed_model_inputs[slot].models+i;
  memcpy(g->models[i].identity,m->identity,20);memcpy(g->models[i].inputs,m->inputs,560);
  g->models[i].size=m->size;g->models[i].hash=m->hash;
 }
 g->outcomes_enabled=live_model_outcomes_enabled;
 const NFModelOutcomeScene*o=live_model_outcomes.scenes+serial%16;
 if(o->count>64)return 0;
 g->outcome.epoch=o->epoch;g->outcome.serial=o->serial;g->outcome.begin=o->begin;g->outcome.count=o->count;g->outcome.failed=o->failed;
 memcpy(g->outcome.records,o->records,o->count*sizeof(o->records[0]));
 key->epoch=epoch;key->serial=serial;key->begin=begin;key->end=end;key->page=e->page;return 1;
}
size_t nf_android_observer_source_world_take(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,void**owned){
 if(!owned)return 0;*owned=NULL;
 if(!android_geometry_cache_enabled)return nf_android_observer_source_world_take_uncached(epoch,serial,begin,end,owned);
 if(GetCurrentThreadId()!=android_geometry_cache_thread)return 0;
 if(android_geometry_cache_epoch!=nf_native_scene_epoch()){
  nf_android_geometry_cache_reset(0);android_geometry_cache_epoch=nf_native_scene_epoch();
 }
 NFGeometryCacheKey key;NFGeometryProducerGuard guard;
 int guarded=android_geometry_guard(epoch,serial,begin,end,&key,&guard);
 size_t bytes=0;
 if(guarded&&nf_geometry_cache_copy(&android_geometry_cache,&key,&guard,sizeof(guard),owned,&bytes)==1)return bytes;
 if(!guarded)android_geometry_cache_bypasses++;
 bytes=nf_android_observer_source_world_take_uncached(epoch,serial,begin,end,owned);
 if(bytes&&*owned&&guarded)nf_geometry_cache_store(&android_geometry_cache,&key,&guard,sizeof(guard),*owned,bytes);
 return bytes;
}
