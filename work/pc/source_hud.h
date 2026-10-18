#ifndef NF_PC_SOURCE_HUD_H
#define NF_PC_SOURCE_HUD_H
#include "source_frame.h"
typedef struct NFPCHud NFPCHud;
/* One historical row:128-byte registers/header,98304VRAM,1024palette,1024OAM.
   Outputs are atomic on unsupported rows. Original prepared OBJ semantics. */
NFPC_API int nf_pc_hud_row(const void*,size_t,unsigned expected_row,uint32_t colors[240],uint32_t metadata[240],uint32_t parameters[5]);
/* Standalone packed NLP1 layers: validates layout/rows/page references, not
   scene-owner provenance. Use source wrapper for a complete captured frame. */
NFPC_API NFPCHud* nf_pc_hud_decode_layers(const void*,size_t,uint64_t epoch,uint64_t refresh,size_t maximum_retained_bytes);
NFPC_API NFPCHud* nf_pc_source_hud(const NFPCSourceFrame*,size_t maximum_retained_bytes);
NFPC_API void nf_pc_hud_free(NFPCHud*);
/* epoch,refresh,rows,nontransparent OBJ candidate cells,requested bytes */
NFPC_API int nf_pc_hud_info(const NFPCHud*,uint64_t out[5]);
/* 0:240x160RGBA colors,1:240x160RGBA metadata,2:160x5uint32 row parameters.
   Owned immutable views. Row params:backdropRGBA,BGpriority,blend,alpha,brightness.
   Retained budget excludes borrowed inputs and100480-byte decode-row scratch. */
NFPC_API int nf_pc_hud_buffer(const NFPCHud*,unsigned,const void**,size_t*);
#endif
