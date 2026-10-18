#ifndef NF_ORDERED_CAPTURE_H
#define NF_ORDERED_CAPTURE_H
#include <windows.h>
#include <stdio.h>
#include "ordered_scene_submission.h"
#include "stable_scene_submission.h"
static double nf_capture_mark(void){LARGE_INTEGER a,b;QueryPerformanceCounter(&a);QueryPerformanceFrequency(&b);return (double)a.QuadPart*1000/b.QuadPart;}
/* Producer-only four-entry owned cache. Queued frames copy all bytes; they
   retain no cache pointer. Key includes bridge, source epoch and observer version.
   Maximum4*64MiB; retirement happens while source allocator DLL remains loaded. */
static struct {HMODULE bridge;uint64_t epoch,version,hits,misses;unsigned cursor;void(*release)(void*);struct {unsigned serial;void*data;size_t size;} entries[4];} nf_complete_road_cache;
static void nf_complete_road_cache_clear(void){for(unsigned i=0;i<4;i++){if(nf_complete_road_cache.entries[i].data&&nf_complete_road_cache.release)nf_complete_road_cache.release(nf_complete_road_cache.entries[i].data);memset(nf_complete_road_cache.entries+i,0,sizeof(nf_complete_road_cache.entries[i]));}nf_complete_road_cache.bridge=NULL;nf_complete_road_cache.cursor=0;}
static int nf_complete_road_acquire(HMODULE bridge,uint64_t epoch,unsigned serial,void**out,size_t*size,int*cached){
 int(*get)(uint64_t,unsigned,void**,size_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_road_bundle");void(*release)(void*)=(void*)GetProcAddress(bridge,"nf_live_ordered_bundle_free");if(!get||!release||!out||!size||!cached)return 0;*cached=0;if(!getenv("NF_TEST_COMPLETE_ROAD_CACHE"))return get(epoch,serial,out,size);
 uint64_t(*version_read)(void)=(void*)GetProcAddress(bridge,"nf_page_write_audit_version");if(!version_read)return 0;uint64_t version=version_read();
 if(nf_complete_road_cache.bridge!=bridge||nf_complete_road_cache.epoch!=epoch||nf_complete_road_cache.version!=version){nf_complete_road_cache_clear();nf_complete_road_cache.bridge=bridge;nf_complete_road_cache.epoch=epoch;nf_complete_road_cache.version=version;nf_complete_road_cache.release=release;}
 for(unsigned i=0;i<4;i++)if(nf_complete_road_cache.entries[i].data&&nf_complete_road_cache.entries[i].serial==serial){*out=nf_complete_road_cache.entries[i].data;*size=nf_complete_road_cache.entries[i].size;*cached=1;nf_complete_road_cache.hits++;return 1;}
 int profile=getenv("NF_TEST_COMPLETE_CAPTURE_PROFILE")!=NULL;double start=profile?nf_capture_mark():0;
 void*data=NULL;size_t bytes=0;NFRoadBundle view;if(!get(epoch,serial,&data,&bytes))return 0;double built=profile?nf_capture_mark():0;if(bytes>64*1024*1024||!nf_road_bundle_view(data,bytes,&view)||view.ordered.epoch!=epoch||view.ordered.packet.serial!=serial){release(data);return 0;}
 if(profile)printf("road_cache_miss_ms serial=%u bytes=%llu build=%.6f validate=%.6f\n",serial,(unsigned long long)bytes,built-start,nf_capture_mark()-built);
 unsigned slot=nf_complete_road_cache.cursor++%4;if(nf_complete_road_cache.entries[slot].data)release(nf_complete_road_cache.entries[slot].data);nf_complete_road_cache.entries[slot].serial=serial;nf_complete_road_cache.entries[slot].data=data;nf_complete_road_cache.entries[slot].size=bytes;nf_complete_road_cache.misses++;*out=data;*size=bytes;*cached=1;return 1;
}
/* Producer thread only. Bridge owners are released before returning the
   immutable combined allocation. Missing any row rejects the whole capture. */
static int nf_ordered_capture(HMODULE bridge,uint64_t epoch,unsigned older,unsigned newer,unsigned refresh,unsigned cut,NFOrderedSceneSubmission**out){
 int(*bundle)(uint64_t,unsigned,void**,size_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_road_bundle");
 void(*release)(void*)=(void*)GetProcAddress(bridge,"nf_live_ordered_bundle_free");
 int(*hud_row)(uint64_t,unsigned,unsigned,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_hud_row");
 int(*text_row)(uint64_t,unsigned,unsigned,void*,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_text_row");
 if(!out||!epoch||!bundle||!release||!hud_row||!text_row)return 0;
 void*a=NULL,*b=NULL;size_t an=0,bn=0;uint8_t*h=malloc(160*sizeof(NFHudLayerRow)),*t=malloc(76832);int ok=0,acached=0,bcached=0;
 if(!h||!t||!nf_complete_road_acquire(bridge,epoch,older,&a,&an,&acached)||!nf_complete_road_acquire(bridge,epoch,newer,&b,&bn,&bcached))goto done;
 uint32_t head[8]={0x5854464e,1,(uint32_t)epoch,(uint32_t)(epoch>>32),refresh,240,160,38400};memcpy(t,head,32);
 for(unsigned y=0;y<160;y++)if(!hud_row(epoch,refresh,y,h+y*sizeof(NFHudLayerRow),sizeof(NFHudLayerRow))||!text_row(epoch,refresh,y,t+32+y*240,t+32+38400+y*240,240))goto done;
 ok=nf_ordered_scene_submission_create(a,an,b,bn,h,160*sizeof(NFHudLayerRow),t,76832,cut,out);
 done:if(a&&!acached)release(a);if(b&&!bcached)release(b);free(h);free(t);return ok;
}
static int nf_stable_capture(HMODULE bridge,const NFPagePersistenceProof*proof,NFStableSceneSubmission**out){
 int(*bundle)(uint64_t,unsigned,void**,size_t*)=(void*)GetProcAddress(bridge,"nf_live_completed_road_bundle");void(*release)(void*)=(void*)GetProcAddress(bridge,"nf_live_ordered_bundle_free");int(*hud_row)(uint64_t,unsigned,unsigned,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_hud_row");int(*text_row)(uint64_t,unsigned,unsigned,void*,void*,unsigned)=(void*)GetProcAddress(bridge,"nf_layer_queue_text_row");int(*generation)(uint64_t,unsigned,unsigned,uint64_t*)=(void*)GetProcAddress(bridge,"nf_layer_queue_page_generation");
 if(!proof||!out||!bundle||!release||!hud_row||!text_row||!generation||proof->page>1)return 0;uint64_t before,after;if(!generation(proof->epoch,proof->display_refresh,proof->page,&before)||before!=proof->display_generation)return 0;
 int profile=getenv("NF_TEST_COMPLETE_CAPTURE_PROFILE")!=NULL;double t0=profile?nf_capture_mark():0,t1=0,t2=0;uint64_t hits_before=nf_complete_road_cache.hits;
 void*b=NULL;size_t bn=0;uint8_t*h=malloc(160*sizeof(NFHudLayerRow)),*t=malloc(76832);NFStableSceneSubmission*s=NULL;int ok=0,bcached=0;if(!h||!t||!nf_complete_road_acquire(bridge,proof->epoch,proof->serial,&b,&bn,&bcached))goto done;
 if(profile)t1=nf_capture_mark();
 uint32_t head[8]={0x5854464e,1,(uint32_t)proof->epoch,(uint32_t)(proof->epoch>>32),proof->display_refresh,240,160,38400};memcpy(t,head,32);
 for(unsigned y=0;y<160;y++)if(!hud_row(proof->epoch,proof->display_refresh,y,h+y*sizeof(NFHudLayerRow),sizeof(NFHudLayerRow))||!text_row(proof->epoch,proof->display_refresh,y,t+32+y*240,t+38432+y*240,240))goto done;
 if(profile)t2=nf_capture_mark();
 if(!nf_stable_scene_create(b,bn,h,160*sizeof(NFHudLayerRow),t,76832,proof,&s)||!generation(proof->epoch,proof->display_refresh,proof->page,&after)||after!=before)goto done;*out=s;s=NULL;ok=1;
 done:if(profile&&ok)printf("stable_capture_stage_ms serial=%u refresh=%u cache_hit=%u acquire=%.6f rows=%.6f clone=%.6f\n",proof->serial,proof->display_refresh,nf_complete_road_cache.hits>hits_before,t1-t0,t2-t1,nf_capture_mark()-t2);nf_stable_scene_destroy(s);if(b&&!bcached)release(b);free(h);free(t);return ok;
}
#endif
