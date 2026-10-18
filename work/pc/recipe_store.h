#ifndef NF_PC_RECIPE_STORE_H
#define NF_PC_RECIPE_STORE_H
#include <stdint.h>
#include <stddef.h>
#ifdef _WIN32
#define NFR_API __declspec(dllexport)
#else
#define NFR_API __attribute__((visibility("default")))
#endif
typedef struct NFRecipeStore NFRecipeStore;
typedef struct NFRecipeSnapshot NFRecipeSnapshot;
typedef struct {const void*data;size_t bytes;} NFRecipeBlock;
/* Keys are {kind, original accepted history ordinal}; epoch is explicit.
   Store mutations/read stats require its owner thread. Snapshot bytes are
   immutable and readable/freeable on another thread. All allocations, including
   surviving snapshots after reset/close, count against one shared budget. */
NFR_API size_t nf_recipe_store_minimum(void);
NFR_API NFRecipeStore*nf_recipe_store_open(uint64_t epoch,size_t maximum);
NFR_API void nf_recipe_store_close(NFRecipeStore*);
NFR_API int nf_recipe_store_put(NFRecipeStore*,uint64_t epoch,unsigned kind,uint64_t ordinal,const NFRecipeBlock*,unsigned count);
NFR_API int nf_recipe_store_prune(NFRecipeStore*,uint64_t epoch,const uint64_t*keys,size_t count);
NFR_API int nf_recipe_store_reset(NFRecipeStore*,uint64_t epoch);
NFR_API int nf_recipe_store_info(NFRecipeStore*,uint64_t out[5]);
NFR_API NFRecipeSnapshot*nf_recipe_store_snapshot(NFRecipeStore*,uint64_t epoch,const uint64_t*keys,size_t count);
NFR_API void nf_recipe_snapshot_free(NFRecipeSnapshot*);
NFR_API int nf_recipe_snapshot_info(const NFRecipeSnapshot*,uint64_t out[5]);
NFR_API int nf_recipe_snapshot_writer(const NFRecipeSnapshot*,size_t index,uint64_t out[3]);
NFR_API int nf_recipe_snapshot_block(const NFRecipeSnapshot*,size_t index,unsigned block,const void**out,size_t*bytes);
#endif
