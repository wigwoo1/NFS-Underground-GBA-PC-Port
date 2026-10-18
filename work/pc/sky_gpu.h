#ifndef NF_PC_SKY_GPU_H
#define NF_PC_SKY_GPU_H
#include "scene_gpu.h"
/* Isolated sky pass/readback diagnostic. Source spans15136bytes; historical
   RGBA palette256x160. Blends palette COLORS using rounded Q16 weight.
   Exact integer pixel-center coverage, including original16-byte tail.
   Clears target; this entry is not a complete scene or live scheduling API. */
NFPC_API int nf_pc_scene_gpu_draw_sky(NFPCSceneGPU*,const void*,size_t,const void*,size_t,double,const void*,size_t,unsigned,unsigned,unsigned,unsigned,unsigned top,unsigned bottom,void*,size_t);
#endif
