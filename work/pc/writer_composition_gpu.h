#ifndef NF_PC_WRITER_COMPOSITION_GPU_H
#define NF_PC_WRITER_COMPOSITION_GPU_H
#include "writer_band_gpu.h"
typedef struct {unsigned owner,count,endpoint,reserved;unsigned bounds[4];double ring[36];const NFPCRecipeWriter*writer;const NFPCWriterAddressMap*map;} NFPCSceneWriterDraw;
/* Synchronous borrowed immutable draw list; caller retains all handles through
   return. Replaces baseline retained-layer stage, preserving background,
   ordered main geometry and HUD. Caller supplies COMPLETE road+wall coverage.
   Only retained rings can move here: main scene remains its captured endpoint.
   No complete-scene fractional-motion claim. No game/core callbacks. */
NFPC_API int nf_pc_scene_gpu_draw_source_writers(NFPCSceneGPU*,NFPCScene*,unsigned width,unsigned height,unsigned active_width,unsigned active_height,const NFPCSceneWriterDraw*,size_t count,void*out,size_t bytes);
/* Same composition without CPU readback; target stays available for present. */
NFPC_API int nf_pc_scene_gpu_render_source_writers(NFPCSceneGPU*,NFPCScene*,unsigned,unsigned,unsigned,unsigned,const NFPCSceneWriterDraw*,size_t);
#endif
