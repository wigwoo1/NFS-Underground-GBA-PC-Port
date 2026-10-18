#ifndef NF_PC_WORLD_MATERIAL_H
#define NF_PC_WORLD_MATERIAL_H
#include "world_mesh.h"
typedef struct NFPCWorldMaterial NFPCWorldMaterial;
/* Owns source planes and one expanded upload image after world/frame release.
   Retained-byte budget excludes temporary mesh preparation. Exclusive caller
   owns mutation; upload view is overwritten by the next level request. */
NFPC_API NFPCWorldMaterial* nf_pc_world_material(const NFPCWorld*,unsigned surface,size_t maximum_bytes);
NFPC_API void nf_pc_world_material_free(NFPCWorldMaterial*);
/* width,height,kind,mode,indexed,lit,has curve,retained requested bytes */
NFPC_API int nf_pc_world_material_info(const NFPCWorldMaterial*,uint64_t out[8]);
NFPC_API int nf_pc_world_material_image(NFPCWorldMaterial*,unsigned level,const void**,size_t*);
/* x0,x1,z0,z1,shade0,shade1. Empty hidden curve rejects. */
NFPC_API int nf_pc_world_material_curve(const NFPCWorldMaterial*,double out[6]);
NFPC_API int nf_pc_world_material_columns(const NFPCWorldMaterial*,unsigned count,uint32_t*out,size_t bytes);
#endif
