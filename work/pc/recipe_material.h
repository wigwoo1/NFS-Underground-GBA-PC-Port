#ifndef NF_PC_RECIPE_MATERIAL_H
#define NF_PC_RECIPE_MATERIAL_H
#include "recipe_store.h"
typedef struct NFPCRecipeMaterial NFPCRecipeMaterial;
/* Fifteen canonical producer/store blocks. Wall material is ONE original
   writer's effective shade remap, not a regenerated whole-wall light field. */
NFR_API NFPCRecipeMaterial*nf_pc_recipe_material_decode(unsigned kind,const NFRecipeBlock*,unsigned count,size_t maximum);
NFR_API void nf_pc_recipe_material_free(NFPCRecipeMaterial*);
/* kind,width,height,shaded,bytes */
NFR_API int nf_pc_recipe_material_info(const NFPCRecipeMaterial*,uint64_t out[5]);
/* indices,states(0skip,1write0,2writeNZ),indexed RGBA(r=index,a=coverage). */
NFR_API int nf_pc_recipe_material_buffer(const NFPCRecipeMaterial*,unsigned,const void**,size_t*);
#endif
