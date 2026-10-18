#ifndef NF_PC_WORLD_CAMERA_MOTION_H
#define NF_PC_WORLD_CAMERA_MOTION_H
#include "source_frame.h"
typedef struct {uint64_t epoch;uint32_t refresh,identity[5];} NFPCWorldMotionKey;
/* Source camera component only. Original source identity, no screen matching.
   Output stays untouched on rejection. Same epoch/key, forward gap<=8, alpha0..1.
   Camera blobs are original version/address/Q14 matrix,56bytes. Matrix sampling
   uses existing recovered view convention; translation/rotation remain quantized.
   Header/state and exact endpoints are discrete. Does not prove smooth motion. */
NFPC_API int nf_pc_world_camera_sample(const void*,size_t,const NFPCWorldMotionKey*,const void*,size_t,const NFPCWorldMotionKey*,double,void*,size_t);
/* Samples then applies unchanged fixed-point road camera to static source world
   points. No projection/material/visibility interpolation or core writes. */
NFPC_API int nf_pc_world_camera_points(const void*,size_t,const NFPCWorldMotionKey*,const void*,size_t,const NFPCWorldMotionKey*,double,const double*,unsigned,double*);
/* NFM2 common camera position/quaternion (7doubles), for world packets without
   optional fixed camera records. Recomputes camera-space source world points.
   Does not apply projection, near clipping or visibility. */
NFPC_API int nf_pc_world_rigid_points(const void*,size_t,const NFPCWorldMotionKey*,const void*,size_t,const NFPCWorldMotionKey*,double,const double*,unsigned,double*);
#endif
