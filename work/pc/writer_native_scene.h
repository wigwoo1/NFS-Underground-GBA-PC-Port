#ifndef NF_PC_WRITER_NATIVE_SCENE_H
#define NF_PC_WRITER_NATIVE_SCENE_H
#include "writer_composition_gpu.h"
#include "writer_shared.h"
typedef struct NFPCWriterNativeScene NFPCWriterNativeScene;
/* Borrow immutable frame and matching recipe snapshots only during prepare.
   Owns endpoint scene, complete writer list, shared assets and address maps.
   One retained budget covers all published allocations, including constructor
   store metadata peak; existing decode/partition/lookup scratch is excluded.
   No core callbacks/steps. May render/read/free on another worker after return. */
NFPC_API NFPCWriterNativeScene*nf_pc_writer_native_scene_prepare(const NFPCSourceFrame*,const NFRecipeSnapshot*const views[2],size_t maximum);
NFPC_API void nf_pc_writer_native_scene_free(NFPCWriterNativeScene*);
/* epoch,refresh,owners,packets,bindings,cells,external bytes,shared bytes,
   combined retained bytes,constructor peak retained bytes */
NFPC_API int nf_pc_writer_native_scene_info(const NFPCWriterNativeScene*,uint64_t out[10]);
NFPC_API int nf_pc_writer_native_scene_draw(NFPCSceneGPU*,NFPCWriterNativeScene*,unsigned,unsigned,unsigned,unsigned,void*,size_t);
NFPC_API int nf_pc_writer_native_scene_render(NFPCSceneGPU*,NFPCWriterNativeScene*,unsigned,unsigned,unsigned,unsigned);
int nf_pc_writer_store_set_maximum(NFRecipeStore*,size_t);
#endif
