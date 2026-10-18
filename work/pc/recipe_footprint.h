#ifndef NF_PC_RECIPE_FOOTPRINT_H
#define NF_PC_RECIPE_FOOTPRINT_H
#include "recipe_geometry.h"
typedef struct NFPCRecipeFootprint NFPCRecipeFootprint;
/* Own the supporting plane and continuous raw Q14 source-camera inverse.
   Caller's exact coverage binding supplies accepted ordinal/write refresh.
   Does not clamp quantized retained border cells to the ideal source polygon.
   No material UV/visibility/occlusion policy inferred. */
NFR_API NFPCRecipeFootprint*nf_pc_recipe_footprint_create(const NFPCRecipeGeometry*,uint64_t ordinal,unsigned write_refresh,const double source_projection[3],size_t maximum);
NFR_API void nf_pc_recipe_footprint_free(NFPCRecipeFootprint*);
/* epoch,recipe-kind,ordinal,source-capture-refresh,accepted-write-refresh,bytes */
NFR_API int nf_pc_recipe_footprint_info(const NFPCRecipeFootprint*,uint64_t out[6]);
/* Source screen point -> world XYZ plus positive source-camera depth.
   Entire support plane, including quantized boundary extensions. */
NFR_API int nf_pc_recipe_footprint_lift(const NFPCRecipeFootprint*,double x,double y,double out[4]);
/* Continuous raw-camera reprojection, NOT original rounded integer projection. */
NFR_API int nf_pc_recipe_footprint_source(const NFPCRecipeFootprint*,const double world[3],double out[3]);
/* Lift then sample common rigid camera. Output camera XYZ before near clipping.
   Temporal eligibility uses accepted WRITE refresh, separate from source capture. */
NFR_API int nf_pc_recipe_footprint_sample(const NFPCRecipeFootprint*,const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double alpha,double source_x,double source_y,double out[3]);
/* Owner-endpoint anchoring: preserve the exact retained screen region at its
   displayed owner, rather than relocating it to an older writer-camera view.
   Owner must exactly equal A or B. B coverage is unavailable before alpha1;
   A coverage may be transported to B for diagnostics, not used as proof of B. */
NFR_API int nf_pc_recipe_footprint_lift_pose(const NFPCRecipeFootprint*,const NFRigidPose*,double x,double y,double out[4]);
NFR_API int nf_pc_recipe_footprint_sample_anchored(const NFPCRecipeFootprint*,const uint64_t coverage_owner[5],const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double alpha,double x,double y,double out[3]);
#endif
