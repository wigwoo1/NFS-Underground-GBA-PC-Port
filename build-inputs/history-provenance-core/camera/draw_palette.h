#ifndef NF_DRAW_PALETTE_H
#define NF_DRAW_PALETTE_H
#include <stdint.h>
#include <stddef.h>
typedef struct NFDrawPalettes NFDrawPalettes;
/* One scene; append order is draw identity. 64 unique BG palettes,256 draws.
   Owns all bytes. Seal before reads/publication. No inferred material aliases. */
__declspec(dllexport) NFDrawPalettes* nf_draw_palettes_create(uint64_t epoch,uint32_t serial);
__declspec(dllexport) void nf_draw_palettes_destroy(NFDrawPalettes*);
__declspec(dllexport) int nf_draw_palettes_append(NFDrawPalettes*,uint32_t kind,uint32_t source,uint32_t material,const void*palette,size_t size);
__declspec(dllexport) int nf_draw_palettes_seal(NFDrawPalettes*);
__declspec(dllexport) int nf_draw_palettes_read(const NFDrawPalettes*,uint64_t epoch,uint32_t serial,unsigned draw,uint32_t kind,uint32_t source,uint32_t material,void*out,size_t size);
__declspec(dllexport) int nf_draw_palettes_info(const NFDrawPalettes*,unsigned*out_draws,unsigned*out_palettes,size_t*out_bytes);
__declspec(dllexport) int nf_draw_palettes_key(const NFDrawPalettes*,unsigned draw,uint32_t out[3]);
#endif
