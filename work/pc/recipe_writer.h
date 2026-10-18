#ifndef NF_PC_RECIPE_WRITER_H
#define NF_PC_RECIPE_WRITER_H
#include "recipe_store.h"
typedef struct NFPCRecipeWriter NFPCRecipeWriter;
/* Exact accepted command from fifteen canonical snapshot blocks. Owns command,
   raw source texture/shade/palette/material bytes; no framebuffer/core access.
   This is original integer writer sampling, NOT authored continuous face UV. */
NFR_API NFPCRecipeWriter*nf_pc_recipe_writer_decode(const uint64_t owner[5],unsigned kind,uint64_t ordinal,unsigned write_refresh,const NFRecipeBlock*,unsigned count,size_t maximum);
NFR_API void nf_pc_recipe_writer_free(NFPCRecipeWriter*);
/* owner5,recipe-kind,ordinal,source-capture-refresh,write-refresh,retained bytes */
NFR_API int nf_pc_recipe_writer_info(const NFPCRecipeWriter*,uint64_t out[10]);
/* command,texture,shade(one byte for unshaded),source palette512,material48 */
NFR_API int nf_pc_recipe_writer_buffer(const NFPCRecipeWriter*,unsigned,const void**,size_t*);
/* Integer owner-source pixel; output raw source offset,index,mapped index,state.
   state0=no write,1=opaque mapped0,2=opaque nonzero. No-write offset UINT64_MAX.
   Wall source0 skips before shading; road byte lanes remain distinct. */
NFR_API int nf_pc_recipe_writer_cell(const NFPCRecipeWriter*,unsigned x,unsigned y,uint64_t out[4]);
#endif
