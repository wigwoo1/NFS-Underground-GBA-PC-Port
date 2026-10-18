#ifndef NF_PC_SOURCE_ROAD_H
#define NF_PC_SOURCE_ROAD_H
#include "source_frame.h"
/* Original fixed-point source math. Tables are 32768 little-endian uint32 words.
   Outputs remain unchanged on errors; no core callbacks or GPU dependencies. */
NFPC_API int nf_pc_road_camera(const void*camera,size_t,const double point[3],double out[3]);
NFPC_API int nf_pc_road_vertex(const void*table,double depth,const int32_t attributes[2],unsigned shift,unsigned height,unsigned affine,double out[2]);
NFPC_API int nf_pc_road_near(const void*table,double z0,double z1,const int32_t attributes[4],unsigned shift,unsigned height,unsigned affine,int near,double out[2]);
NFPC_API int nf_pc_road_clip(const void*table,const double*camera,unsigned count,const void*attributes,size_t,double out[64][5],unsigned*out_count);
NFPC_API int nf_pc_road_project_point(const void*table,const double point[3],const double attributes[2],unsigned shift,unsigned height,const int32_t projection[3],double out[5]);
NFPC_API int nf_pc_road_project_near(const void*table,const double a[5],const double b[5],double near,double out[5]);
NFPC_API int nf_pc_road_project_ring(const void*table,const double*world,unsigned count,const void*attributes,size_t,const void*camera,size_t,const int32_t projection[3],double out[64][5],unsigned*out_count);
#endif
