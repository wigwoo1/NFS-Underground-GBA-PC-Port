#ifndef NF_PC_RECIPE_GPU_H
#define NF_PC_RECIPE_GPU_H
#include "scene_gpu.h"
#include "recipe_mesh.h"
#include "recipe_material.h"
/* Existing target only. Clip left/right/top/bottom in source cells, exclusive
   right/bottom. Caller explicitly orders submissions and defines coverage.
   No clear, allocation of target, readback, core callback or visibility inference. */
NFPC_API int nf_pc_scene_gpu_render_recipe(NFPCSceneGPU*,const NFPCRecipeMesh*,const NFPCRecipeMaterial*,const void*row_palette,size_t,unsigned active_width,unsigned active_height,const unsigned clip[4]);
#endif
