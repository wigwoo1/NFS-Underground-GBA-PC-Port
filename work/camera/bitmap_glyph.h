#ifndef NF_BITMAP_GLYPH_H
#define NF_BITMAP_GLYPH_H
#include <stdint.h>
#include <stddef.h>
typedef struct {uint32_t width,height,draw_width,stride,flags,transparent,palette_offset;} NFBitmapGlyph;
/* Bounded owned asset decoder. outputs width*height source indices plus write
   coverage; never reads a rendered framebuffer. All outputs atomic on failure. */
__declspec(dllexport) int nf_bitmap_glyph_decode(const NFBitmapGlyph*,const uint8_t*,size_t,uint8_t*,uint8_t*,size_t);
#endif
