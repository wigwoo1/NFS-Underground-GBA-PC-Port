#include <stdint.h>
#include <string.h>
#include "layer_snapshot.h"
static NFHudLayerRow sky_hud_cached_rows[160];static const NFHudLayerRow*owned_hud;static uint32_t hud_refresh;
static int hud_visual_rows_equal(void){
 for(unsigned y=0;y<160;y++){
  const NFHudLayerRow*a=sky_hud_cached_rows+y,*b=owned_hud+y;
  if(b->refresh!=hud_refresh||b->row!=y||a->row!=y)return 0;
  if(memcmp((const uint8_t*)a+8,(const uint8_t*)b+8,sizeof(*a)-8))return 0;
 }
 return 1;
}
__declspec(dllexport) int nf_test_hud_equal(const void*a,const void*b,uint32_t refresh){if(!a||!b)return 0;memcpy(sky_hud_cached_rows,a,sizeof(sky_hud_cached_rows));owned_hud=b;hud_refresh=refresh;return hud_visual_rows_equal();}
__declspec(dllexport) unsigned nf_test_hud_row_size(void){return sizeof(NFHudLayerRow);}
