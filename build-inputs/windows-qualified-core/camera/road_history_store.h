#ifndef NF_ROAD_HISTORY_STORE_H
#define NF_ROAD_HISTORY_STORE_H
#include "native_scene_executor.h"
/* Bounded original affine-run history; only last-road source references retained.
   Non-road overwrite proof is separate. Snapshot NRH1 shares immutable assets. */
void *nf_road_history_create(uint64_t,size_t);
void nf_road_history_destroy(void*);
int nf_road_history_reset(void*,uint64_t);
int nf_road_history_append(void*,uint64_t,uint64_t,unsigned,const NFSceneEvent*);
size_t nf_road_history_snapshot(void*,uint64_t,void*,size_t);
int nf_road_history_stats(void*,uint64_t[5]);
#endif
