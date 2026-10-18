#ifndef NF_PC_SKY_COMPOSITION_H
#define NF_PC_SKY_COMPOSITION_H
#include "sky_gpu.h"
/* Owner-thread submission into an ALREADY INITIALIZED target of matching size.
   Preserves pixels outside the source sky footprint and [top,bottom) band.
   Does not clear, resize, finish, read back, or advance game logic.
   Caller must establish scene order and owner/palette/alpha consistency. */
NFPC_API int nf_pc_scene_gpu_render_sky(NFPCSceneGPU*,const void*,size_t,const void*,size_t,double,const void*,size_t,unsigned,unsigned,unsigned,unsigned,unsigned top,unsigned bottom);
/* Separate diagnostic readback of the current target, bottom row first. */
NFPC_API int nf_pc_scene_gpu_read_target(NFPCSceneGPU*,void*,size_t);
#endif
