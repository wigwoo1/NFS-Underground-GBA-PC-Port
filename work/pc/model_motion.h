#ifndef NF_PC_MODEL_MOTION_H
#define NF_PC_MODEL_MOTION_H
#include "model_mesh.h"
typedef struct {uint64_t epoch;uint32_t refresh,identity[5];} NFPCModelMotionKey;
/* Component only, not full-scene interpolation. Match explicit SOURCE identity,
   never projected polygons. Requires identical model-local geometry/UV bytes,
   same epoch, and forward source refresh gap <=8. Materials stay at older
   source values until the exact newer endpoint. Rebuilds projection,
   near clipping and culling from sampled camera/object poses. No core writes.
   Result owns its storage; alpha0/1 preserve exact decoded endpoint buffers. */
NFPC_API NFPCModelMesh* nf_pc_model_motion_sample(const void*,size_t,const NFPCModelMotionKey*,const void*,size_t,const NFPCModelMotionKey*,double alpha,size_t maximum_bytes);
#endif
