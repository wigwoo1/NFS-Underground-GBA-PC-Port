#ifndef NF_PC_WRITER_SCENE_GPU_H
#define NF_PC_WRITER_SCENE_GPU_H
#include "writer_gpu.h"
#include "source_scene.h"
/* Bind the immutable display scene palette, after exact owner-key validation.
   Bounds must belong to this scene owner's original display band. This isolated
   pass does not establish fractional destination band clipping or scene order. */
NFPC_API int nf_pc_scene_gpu_render_scene_writer(NFPCSceneGPU*,const NFPCScene*,unsigned owner,const double*ring,unsigned count,const unsigned bounds[4],const NFPCRecipeWriter*,const NFPCWriterAddressMap*,unsigned active_width,unsigned active_height,unsigned exact_owner_endpoint);
#endif
