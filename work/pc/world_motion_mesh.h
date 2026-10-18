#ifndef NF_PC_WORLD_MOTION_MESH_H
#define NF_PC_WORLD_MOTION_MESH_H
#include "world_mesh.h"
#include "world_camera_motion.h"
/* Component constructor. Explicit source identity must agree with each selected
   source surface. Static world vertices/UV/layout must agree. Common NFM camera
   only; optional fixed-camera records reject. Samples camera/projection in an
   owned older packet, then reuses unchanged world mesh clipping/UV/triangulation.
   Material,command order/scissor stay older until exact newer endpoint.
   Per-result mesh budget; temporary validated packets are separately bounded.
   Not a visibility/retention/full-scene sampler. */
NFPC_API NFPCWorldMesh* nf_pc_world_motion_mesh(const void*,size_t,unsigned,const NFPCWorldMotionKey*,const void*,size_t,unsigned,const NFPCWorldMotionKey*,double,size_t);
#endif
