#ifndef NF_PC_SOURCE_BACKGROUND_H
#define NF_PC_SOURCE_BACKGROUND_H
#include "source_frame.h"
/* Source-index/palette expansion only, never the original displayed framebuffer.
   Background/sky: 240*160*4 top-down RGBA; palette: 256*160*4 RGBA.
   Uncovered source cells stay transparent. Buffer errors leave output unchanged. */
NFPC_API int nf_pc_source_palette_rgba(const NFPCSourceFrame*,void*,size_t);
NFPC_API int nf_pc_source_background_rgba(const NFPCSourceFrame*,void*,size_t);
NFPC_API int nf_pc_source_sky_rgba(const NFPCSourceFrame*,void*,size_t);
#endif
