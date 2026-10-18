#ifndef NF_OWNED_ROAD_SOURCE_H
#define NF_OWNED_ROAD_SOURCE_H
#include <windows.h>
#include <limits.h>
#include <stdlib.h>
#include "road_bundle.h"
/* One private heap copy, independent of the bridge allocator and DLL lifetime.
   Canonical pointers remain valid until the final retained reference retires.
   Callers may retain only while they already hold a live reference. */
typedef struct {volatile LONG references;uint64_t epoch,observer_version;unsigned serial;size_t size;NFRoadBundle view;uint8_t bytes[];} NFOwnedRoadSource;
static int nf_owned_road_source_create(const void*data,size_t size,uint64_t epoch,uint64_t observer_version,unsigned serial,NFOwnedRoadSource**out){
 if(!out||!data||!epoch||!observer_version||size>64*1024*1024||size>SIZE_MAX-sizeof(NFOwnedRoadSource))return 0;
 NFRoadBundle input;if(!nf_road_bundle_view(data,size,&input)||input.ordered.epoch!=epoch||input.ordered.packet.serial!=serial)return 0;
 NFOwnedRoadSource*s=malloc(sizeof(*s)+size);if(!s)return 0;s->references=1;s->epoch=epoch;s->observer_version=observer_version;s->serial=serial;s->size=size;memcpy(s->bytes,data,size);
 if(!nf_road_bundle_view(s->bytes,size,&s->view)){free(s);return 0;}*out=s;return 1;
}
static int nf_owned_road_source_retain(NFOwnedRoadSource*s){if(!s)return 0;LONG count=InterlockedCompareExchange(&s->references,0,0);while(count>0&&count<LONG_MAX){LONG previous=InterlockedCompareExchange(&s->references,count+1,count);if(previous==count)return 1;count=previous;}return 0;}
static void nf_owned_road_source_release(NFOwnedRoadSource*s){if(s&&InterlockedDecrement(&s->references)==0)free(s);}
static const NFRoadBundle*nf_owned_road_source_view(const NFOwnedRoadSource*s,uint64_t epoch,uint64_t observer_version,unsigned serial){return s&&s->epoch==epoch&&s->observer_version==observer_version&&s->serial==serial?&s->view:NULL;}
#endif
