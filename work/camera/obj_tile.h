#ifndef NF_OBJ_TILE_H
#define NF_OBJ_TILE_H
#include <stdint.h>
#include <stddef.h>
/* One original OBJ tile; bitmap modes reserve OBJ tile numbers below512.
   Palette index zero is transparent. Output is64RGBA pixels, atomic on failure. */
__declspec(dllexport) int nf_obj_tile(const uint8_t*,size_t,const uint8_t*,size_t,unsigned,unsigned,unsigned,unsigned,uint32_t[64]);
/* Regular sprite image only; rejects affine,disabled,window/reserved modes. */
__declspec(dllexport) int nf_obj_image(const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,uint32_t*,size_t,unsigned[2]);
__declspec(dllexport) int nf_obj_affine_image(const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,const int16_t[4],uint32_t*,size_t,unsigned[2]);
/* Unblended240x160OBJcandidateplane; tagspriority/mode/index,UINT_MAXempty. */
__declspec(dllexport) int nf_obj_layer(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint32_t*,uint32_t*);
/* Exact unblended candidate scanline, including transparent priority updates. */
__declspec(dllexport) int nf_obj_scanline(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,unsigned,uint32_t[240],uint32_t[240]);
/* Palette variants happen before overlap; composition uses tag|0x20000. */
__declspec(dllexport) int nf_obj_scanline_prepared(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,unsigned,unsigned,unsigned,uint32_t[240],uint32_t[240]);
__declspec(dllexport) int nf_obj_layer_prepared(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,unsigned,unsigned,uint32_t*,uint32_t*);
/* Two visible OBJ/BG2 candidates; matches original32bitsoftwarecolor path. */
__declspec(dllexport) uint32_t nf_obj_bg_pixel(uint32_t,uint32_t,uint32_t,unsigned,unsigned,unsigned,unsigned);
/* OBJ, optional BG2 (zero means absent), and opaque backdrop. No windows. */
__declspec(dllexport) uint32_t nf_obj_bg_backdrop_pixel(uint32_t,uint32_t,uint32_t,unsigned,uint32_t,unsigned,unsigned,unsigned);
/* Identity-affine mode4 composition; atomic; windows/mosaic unsupported. */
__declspec(dllexport) int nf_obj_mode4_layer(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,uint32_t*);
/* PA,PB,PC,PD signed8.8; X,Y signed28-bit Q8 references. */
__declspec(dllexport) int nf_obj_mode4_affine_layer(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,const int32_t[6],uint32_t*);
/* WIN0H,WIN1H,WIN0V,WIN1V,WININ,WINOUT; rejects OBJ window. */
__declspec(dllexport) int nf_rect_window_layer(unsigned,const uint16_t[6],uint8_t*);
/* Exact rectangular-window candidates and distinct backdrop alignment controls. */
__declspec(dllexport) int nf_obj_window_scanline_prepared(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,unsigned,const uint16_t[6],unsigned,unsigned,uint32_t[240],uint32_t[240],uint8_t[240],uint8_t[240]);
__declspec(dllexport) int nf_obj_mode4_window_layer(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,const int32_t[6],const uint16_t[6],uint32_t*);
/* Matrix origin is the captured current scanline origin, not frame origin.
   Source asset composition only; output is not a replacement for native 3D. */
__declspec(dllexport) int nf_obj_mode4_window_scanline(const uint8_t*,size_t,const uint8_t*,size_t,const uint8_t*,size_t,uint16_t,uint16_t,uint16_t,uint16_t,uint16_t,const int32_t[6],const uint16_t[6],unsigned,uint32_t[240]);
#endif
