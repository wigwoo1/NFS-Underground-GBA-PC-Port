#ifndef NF_PC_WRITER_GPU_H
#define NF_PC_WRITER_GPU_H
#include "coverage_mask_gpu.h"
#include "writer_address_map.h"
/* Verified projective coverage plus original integer writer sampling from raw
   source assets. Palette is actual display-row state supplied by caller.
   Diagnostic index_mode outputs(index,0,0,255); otherwise palette RGBA colors.
   This reference path does not establish authored subpixel/4K-upscaled UVs. */
NFPC_API int nf_pc_scene_gpu_render_writer(NFPCSceneGPU*,const double*ring,unsigned count,const unsigned bounds[4],const NFPCRecipeWriter*,const NFPCWriterAddressMap*,const void*row_palette,size_t,unsigned active_width,unsigned active_height,unsigned exact_owner_endpoint,unsigned index_mode);
#endif
