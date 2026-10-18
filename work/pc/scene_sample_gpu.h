#ifndef NF_PC_SCENE_SAMPLE_GPU_H
#define NF_PC_SCENE_SAMPLE_GPU_H
#include "scene_gpu.h"
#include "scene_sample.h"
/* Diagnostic source-band composition through the existing four GPU passes.
   Borrowed parents/material caches require exclusive access during submission.
   render_sample has no CPU readback; neither API performs game scheduling. */
NFPC_API int nf_pc_scene_gpu_draw_sample(NFPCSceneGPU*,const NFPCSceneSample*,unsigned,unsigned,unsigned,unsigned,unsigned passes,void*,size_t);
NFPC_API int nf_pc_scene_gpu_render_sample(NFPCSceneGPU*,const NFPCSceneSample*,unsigned,unsigned,unsigned,unsigned);
#endif
