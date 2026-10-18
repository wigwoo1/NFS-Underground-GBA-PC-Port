#ifndef NF_BITMAP_LAYER_H
#define NF_BITMAP_LAYER_H
#include "bitmap_glyph.h"
typedef struct NFBitmapLayer NFBitmapLayer;
__declspec(dllexport) NFBitmapLayer*nf_bitmap_layer_create(uint64_t);
__declspec(dllexport) void nf_bitmap_layer_destroy(NFBitmapLayer*);
__declspec(dllexport) int nf_bitmap_layer_reset(NFBitmapLayer*,uint64_t);
/* Only completed glyph commands; lifecycle/visibility owned by caller. */
__declspec(dllexport) int nf_bitmap_layer_glyph(NFBitmapLayer*,uint64_t,uint32_t,const NFBitmapGlyph*,const uint8_t*,size_t);
__declspec(dllexport) int nf_bitmap_layer_invalidate(NFBitmapLayer*,uint64_t,uint32_t,size_t);
/* Atomic independent plane copy, no borrowed glyph assets or framebuffer. */
__declspec(dllexport) int nf_bitmap_layer_plane(const NFBitmapLayer*,uint64_t,unsigned,uint8_t*,uint8_t*,size_t);
__declspec(dllexport) int nf_bitmap_layer_row(const NFBitmapLayer*,uint64_t,unsigned,unsigned,uint8_t[240],uint8_t[240]);

/* Changed covered bytes only; uses retained asset indices, no live bus reads. */
__declspec(dllexport) unsigned nf_bitmap_layer_changed_mask(const NFBitmapLayer*,uint64_t,uint32_t,uint32_t,unsigned);

#endif
