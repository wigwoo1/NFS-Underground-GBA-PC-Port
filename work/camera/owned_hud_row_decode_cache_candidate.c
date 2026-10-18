#include <stdint.h>
#include <string.h>
#include "layer_snapshot.h"
#include "obj_tile_plane_candidate.h"
typedef struct {uint32_t colors[240],tags[240];uint8_t controls[240],backdrop[240];} NFRowOutput;
static NFHudLayerRow inputs[160];static NFRowOutput outputs[160];static uint8_t valid[160];static uint64_t epoch,hits,misses;
__declspec(dllexport) void nf_hud_row_cache_clear(void){memset(valid,0,sizeof(valid));epoch=0;hits=misses=0;}
__declspec(dllexport) int nf_hud_row_cache_stats(uint64_t*out){if(!out)return 0;out[0]=hits;out[1]=misses;out[2]=sizeof(inputs)+sizeof(outputs)+sizeof(valid);return 1;}
__declspec(dllexport) int nf_hud_row_decode_direct(const NFHudLayerRow*r,NFRowOutput*out){
 if(!r||!out||r->row>=160)return 0;uint16_t w[6];for(unsigned i=0;i<6;i++)memcpy(w+i,r->registers+64+2*i,2);uint16_t display,blend,brightness;memcpy(&display,r->registers,2);memcpy(&blend,r->registers+0x50,2);memcpy(&brightness,r->registers+0x54,2);
 return nf_obj_plane_window_scanline_prepared(r->obj_vram,sizeof(r->obj_vram),r->palette,sizeof(r->palette),r->oam,sizeof(r->oam),display,r->row,w,blend,brightness,out->colors,out->tags,out->controls,out->backdrop);}
__declspec(dllexport) int nf_hud_row_decode_cached(uint64_t e,const NFHudLayerRow*r,NFRowOutput*out){
 if(!e||!r||!out||r->row>=160)return 0;if(epoch!=e){memset(valid,0,sizeof(valid));epoch=e;}unsigned y=r->row;
 /* Exact decoder inputs plus conservative affine/register equality; refresh is metadata. */
 if(valid[y]&&!memcmp((const uint8_t*)(inputs+y)+4,(const uint8_t*)r+4,sizeof(*r)-4)){memcpy(out,outputs+y,sizeof(*out));hits++;return 1;}
 NFRowOutput next;if(!nf_hud_row_decode_direct(r,&next))return 0;inputs[y]=*r;outputs[y]=next;valid[y]=1;misses++;*out=next;return 1;}
