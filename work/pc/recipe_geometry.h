#ifndef NF_PC_RECIPE_GEOMETRY_H
#define NF_PC_RECIPE_GEOMETRY_H
#include "recipe_store.h"
#include "../camera/rigid_motion.h"
typedef struct NFPCRecipeGeometry NFPCRecipeGeometry;
/* Twelve owned producer source blocks; geometry copies numbers only, retains
   no source pointers and does not bind materials or decide visibility/order. */
NFR_API NFPCRecipeGeometry*nf_pc_recipe_geometry_decode(uint64_t epoch,unsigned refresh,unsigned kind,const NFRecipeBlock*,unsigned count,size_t maximum);
NFR_API void nf_pc_recipe_geometry_free(NFPCRecipeGeometry*);
/* epoch,refresh,kind,corners,width,height,source flags,UV supported,bytes */
NFR_API int nf_pc_recipe_geometry_info(const NFPCRecipeGeometry*,uint64_t out[9]);
/* World XYZ doubles,source UV doubles,road attributes288,source matrix48,bounds8 */
NFR_API int nf_pc_recipe_geometry_buffer(const NFPCRecipeGeometry*,unsigned,const void**,size_t*);
/* Complete owner keys; caller supplies the SAME sampled camera as the scene.
   Historical recipes may precede owner A; newer recipes reject before alpha1. */
NFR_API int nf_pc_recipe_geometry_camera(const NFPCRecipeGeometry*,const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double alpha,void*out,size_t bytes);
/* Near64-clipped ring: x,y,depth,u,v,q doubles. No viewport/scissor or
   visibility inference. Road UV projection reuses verified source_road.c.
   Unsupported UV policy rejects atomically; empty clipped ring is success. */
NFR_API int nf_pc_recipe_geometry_project(const NFPCRecipeGeometry*,const uint64_t a[5],const NFRigidPose*,const uint64_t b[5],const NFRigidPose*,double alpha,const double projection[3],const void*reciprocals,size_t table_bytes,void*out,size_t bytes,unsigned*count);
#endif
