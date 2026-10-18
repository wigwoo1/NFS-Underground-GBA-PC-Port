#ifndef NF_PC_WORLD_GPU_H
#define NF_PC_WORLD_GPU_H
#include "world_material.h"
typedef struct NFPCWorldGPU NFPCWorldGPU;
/* Hidden thread-owned context; isolated surface pass, not full composition. */
NFPC_API NFPCWorldGPU* nf_pc_world_gpu_open(void);
NFPC_API void nf_pc_world_gpu_close(NFPCWorldGPU*);
NFPC_API const char* nf_pc_world_gpu_error(void);
NFPC_API const char* nf_pc_world_gpu_renderer(const NFPCWorldGPU*);
/* Mesh/material must come from same world/surface. Clears full target, draws
   bounds intersected with owner rows, returns bottom-up RGBA. Other pixels
   transparent. Caller discards output on failure. Material cache mutates. */
NFPC_API int nf_pc_world_gpu_draw(NFPCWorldGPU*,const NFPCWorldMesh*,NFPCWorldMaterial*,const void*palette,size_t palette_bytes,unsigned width,unsigned height,unsigned active_width,unsigned active_height,unsigned owner_top,unsigned owner_bottom,void*out,size_t bytes);
#endif
