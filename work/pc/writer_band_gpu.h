#ifndef NF_PC_WRITER_BAND_GPU_H
#define NF_PC_WRITER_BAND_GPU_H
#include "writer_scene_gpu.h"
/* Destination half-open rows use the historical palette's integer pixel-center
   classification. This does not establish full-scene ordering/visibility. */
NFPC_API int nf_pc_scene_gpu_render_writer_band(NFPCSceneGPU*,const double*,unsigned,const unsigned[4],const NFPCRecipeWriter*,const NFPCWriterAddressMap*,const void*,size_t,unsigned,unsigned,unsigned,unsigned,unsigned top,unsigned bottom);
NFPC_API int nf_pc_scene_gpu_render_scene_writer_banded(NFPCSceneGPU*,const NFPCScene*,unsigned,const double*,unsigned,const unsigned[4],const NFPCRecipeWriter*,const NFPCWriterAddressMap*,unsigned,unsigned,unsigned);
#endif
