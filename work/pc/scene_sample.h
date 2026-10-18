#ifndef NF_PC_SCENE_SAMPLE_H
#define NF_PC_SCENE_SAMPLE_H
#include "source_scene.h"
typedef struct NFPCSceneSample NFPCSceneSample;
enum {NFPC_SAMPLE_OLDER=0,NFPC_SAMPLE_NEWER=1,NFPC_SAMPLE_INTERIOR=2};
enum {NFPC_SAMPLE_OK=0,NFPC_SAMPLE_ARGUMENT=1,NFPC_SAMPLE_PAIR=2,NFPC_SAMPLE_TIME=3,NFPC_SAMPLE_BUDGET=4,NFPC_SAMPLE_SOURCE=5,NFPC_SAMPLE_HELD=6,NFPC_SAMPLE_BREAK=7};
/* Time range only: intersection of camera/sky brackets of EVERY forward band.
   Held-only pairs reject with HELD; temporal breaks reject with BREAK. Outputs
   unchanged on rejection. Sky asset/geometry support is checked by prepare. */
NFPC_API int nf_pc_scene_sample_range(const NFPCScene*,const NFPCScene*,double*,double*,unsigned*reason);
/* Diagnostic full-target composition plan, not live/full-scene60fps approval.
   Exact endpoint modes retain the complete selected endpoint. Interior uses a
   common target in [rangeStart,rangeEnd), actual capture clocks and original
   source IDs. Held bands/unsupported or old-only commands retain older geometry;
   newer-only commands wait for full newer endpoint. Every case is counted.
   Sky is sampled per band. Retention/HUD/palette/visibility remain older.
   BORROWS both parent scenes: keep them alive and exclude concurrent material
   cache use until plan free/draw complete. Owns all sampled meshes/planes/sky.
   Returned retained budget<=64MiB excludes parents and separately bounded
   constructor scratch (owner64MiB, source pair256KiB, sky64KiB). */
NFPC_API NFPCSceneSample* nf_pc_scene_sample_prepare(NFPCScene*,NFPCScene*,double target,unsigned mode,size_t maximum_retained_bytes,unsigned*reason);
NFPC_API void nf_pc_scene_sample_free(NFPCSceneSample*);
/* epoch,mode,bands,draws,model samples,world samples,sky bands,held draws,
   unsupported draws,old-only draws,unpaired newer rows,break bands,bytes,
   forward bands,held bands,limitation flags(1retention2HUD4visibility8palette/
   materials16per-model-input-time). Target returned separately. */
NFPC_API int nf_pc_scene_sample_info(const NFPCSceneSample*,uint64_t out[16],double*target);
/* top,bottom,old/new owner,temporal mode,first draw,draw count,model samples,
   world samples,held draws,unsupported draws,sky sampled; camera/sky fractions.
   Endpoint modes have one full-height band with owner/mode UINT32_MAX. */
NFPC_API int nf_pc_scene_sample_band(const NFPCSceneSample*,unsigned,uint64_t out[12],double fractions[2]);
/* selected-base command index,band,source-pair status,sample kind(0held1model
   2world),flags(1unsupported2old-only). Original order retained within band. */
NFPC_API int nf_pc_scene_sample_command(const NFPCSceneSample*,unsigned,uint64_t out[5]);
#endif
