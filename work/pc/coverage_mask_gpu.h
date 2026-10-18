#ifndef NF_PC_COVERAGE_MASK_GPU_H
#define NF_PC_COVERAGE_MASK_GPU_H
#include "scene_gpu.h"
/* Diagnostic constant writer color; requires projective owner-screen mask ring.
   Existing target, no clear/readback. Endpoint flag must mean exact coverage
   owner time; uses integer source-cell ownership there. No game-material UV. */
NFPC_API int nf_pc_scene_gpu_render_coverage_mask(NFPCSceneGPU*,const double*ring,unsigned count,const unsigned bounds[4],const unsigned char color[4],unsigned active_width,unsigned active_height,unsigned exact_owner_endpoint);
#endif
