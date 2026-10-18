#ifndef NF_PC_REGION_MASK_H
#define NF_PC_REGION_MASK_H
#include "recipe_regions.h"
/* Source coverage coordinates are projective: u,v are owner-screen pixels;
   q=owner camera depth/current depth. These are mask coordinates, NOT game UVs. */
NFR_API int nf_pc_recipe_region_mask_ring(const NFPCRecipeRegions*,size_t,const NFPCRecipeFootprint*,const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double,const double projection[3],void*,size_t,unsigned*);
#endif
