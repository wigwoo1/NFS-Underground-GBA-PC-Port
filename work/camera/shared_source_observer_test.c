#include "prepared_motion_capture.h"
#include <stdio.h>
int main(void){HMODULE bridge=LoadLibraryA("work/camera/shared-source-mock-bridge.dll");if(!bridge)return 1;void(*reset)(void)=(void*)GetProcAddress(bridge,"nf_mock_observer_reset");void(*during)(void)=(void*)GetProcAddress(bridge,"nf_mock_reset_during_build");if(!reset||!during)return 2;_putenv("NF_TEST_COMPLETE_ROAD_CACHE=1");
 NFOwnedRoadSource*old=NULL,*hit=NULL,*fresh=NULL;if(!nf_shared_road_acquire(bridge,2,18,&old)||!nf_shared_road_acquire(bridge,2,18,&hit)||old!=hit||nf_shared_road_cache.hits!=1)return 3;nf_owned_road_source_release(hit);
 reset();if(!nf_shared_road_acquire(bridge,2,18,&fresh)||fresh==old||fresh->observer_version==old->observer_version||fresh->epoch!=old->epoch||memcmp(old->bytes,fresh->bytes,old->size)||nf_shared_road_cache.clears!=2)return 4;
 nf_shared_road_cache_clear();nf_complete_road_cache_clear();if(old->references!=1||fresh->references!=1)return 5;NFRoadBundle v;if(!nf_road_bundle_view(old->bytes,old->size,&v)||!nf_road_bundle_view(fresh->bytes,fresh->size,&v))return 6;
 during();NFOwnedRoadSource*sentinel=(void*)123;if(nf_shared_road_acquire(bridge,2,18,&sentinel)||sentinel!=(void*)123)return 7;/* observer changed between key read and publication */
 nf_shared_road_cache_clear();nf_complete_road_cache_clear();FreeLibrary(bridge);if(!nf_road_bundle_view(old->bytes,old->size,&v)||!nf_road_bundle_view(fresh->bytes,fresh->size,&v))return 8;
 printf("PASS same_epoch_observer_reset=1 cache_hit=1 distinct_versions_owned=1 retained_after_cache_clear=1 retained_after_bridge_unload=1 mid_build_reset_atomic=1\n");nf_owned_road_source_release(old);nf_owned_road_source_release(fresh);return 0;}
