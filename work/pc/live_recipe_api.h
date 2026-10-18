#ifndef NF_PC_LIVE_RECIPE_API_H
#define NF_PC_LIVE_RECIPE_API_H
#include "recipe_store.h"
/* Core owner thread only. Returns an independently owned snapshot, free with
   nf_recipe_snapshot_free even after checkpoint reset/core close. Key is
   epoch,serial,begin,end,page, exactly as NFPCSourceFrame owner metadata. */
NFR_API NFRecipeSnapshot*nf_pc_live_recipe_acquire(const uint64_t owner[5]);
/* epoch,failed,road,walls,closed,writers,blocks,used,peak,budget,wallDepth */
NFR_API int nf_pc_live_recipe_info(uint64_t out[11]);
#endif
