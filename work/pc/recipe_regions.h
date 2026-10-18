#ifndef NF_PC_RECIPE_REGIONS_H
#define NF_PC_RECIPE_REGIONS_H
#include "recipe_coverage.h"
#include "recipe_footprint.h"
typedef struct NFPCRecipeRegions NFPCRecipeRegions;
/* Merge contiguous horizontal cells of one accepted writer/write refresh;
   vertically merge only identical runs. Exact holes and writer boundaries stay.
   Retained budget excludes temporary worst-case rectangle scratch. */
NFR_API NFPCRecipeRegions*nf_pc_recipe_regions_create(const NFPCRecipeCoverage*,size_t maximum);
NFR_API void nf_pc_recipe_regions_free(NFPCRecipeRegions*);
/* owner[5],NFPC kind,cells,rectangles,retained bytes */
NFR_API int nf_pc_recipe_regions_info(const NFPCRecipeRegions*,uint64_t out[9]);
/* Eight-u64 rectangles:epoch,recipe-kind,ordinal,write-refresh,left,right,top,bottom.
   Geometry partition only; rectangle array order is NOT original painter order. */
NFR_API int nf_pc_recipe_regions_buffer(const NFPCRecipeRegions*,const void**,size_t*);
/* Lift exact boundary corners at coverage owner, sample common camera and
   near64 clip. Ring has x,y,depth,0,0,1/depth doubles; zero UV fields deliberately
   carry NO material mapping. Up to six vertices, at least288 output bytes.
   Newer coverage unavailable before alpha1. No viewport/owner-band reclip or
   occlusion inference at sampled pose; caller composes those policies. */
NFR_API int nf_pc_recipe_regions_ring(const NFPCRecipeRegions*,size_t rectangle,const NFPCRecipeFootprint*,const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double alpha,const double projection[3],void*out,size_t,unsigned*count);
#endif
