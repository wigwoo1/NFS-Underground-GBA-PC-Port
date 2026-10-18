#ifndef NF_WALL_HISTORY_STORE_H
#define NF_WALL_HISTORY_STORE_H
#include "native_scene_executor.h"
/* Owner-thread bounded ORIGINAL wall-command retention. Non-wall overwrite
   proof remains separate. Snapshot is NWH1, not a framebuffer or a live API. */
void *nf_wall_history_create(uint64_t epoch,size_t asset_budget);
void nf_wall_history_destroy(void *);
int nf_wall_history_reset(void *,uint64_t epoch);
int nf_wall_history_append(void *,uint64_t epoch,uint64_t ordinal,unsigned refresh,const NFSceneEvent *);
size_t nf_wall_history_snapshot(void *,uint64_t epoch,void *,size_t);
int nf_wall_history_stats(void *,uint64_t out[5]);
#endif
