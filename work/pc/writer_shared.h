#ifndef NF_PC_WRITER_SHARED_H
#define NF_PC_WRITER_SHARED_H
#include "recipe_writer.h"
/* Store and writer must use this module. Its existing ledger counts shared raw
   blobs, snapshot references AND thin writer allocations. Store owner thread
   constructs; immutable writer may outlive store and be freed on a worker.
   Existing store block limit1MiB applies. Temporary validation copy excluded.
   Failure may leave reusable interned assets in store, never a published writer.
   info[9] is this writer allocation+snapshot descriptor, excludes shared assets;
   store_info[3] is authoritative combined allocation (not RSS/GPU/temporary). */
NFR_API NFPCRecipeWriter*nf_pc_recipe_writer_decode_shared(NFRecipeStore*,const uint64_t owner[5],unsigned kind,uint64_t ordinal,unsigned write,const NFRecipeBlock*,unsigned count);
NFR_API int nf_pc_recipe_writer_shared_info(const NFPCRecipeWriter*,uint64_t out[5]);
/* Internal allocator on the EXISTING store ledger; do not free with free(). */
void*nf_pc_writer_ledger_allocate(NFRecipeStore*,size_t,size_t*charged);
void nf_pc_writer_ledger_free(void*);
#endif
