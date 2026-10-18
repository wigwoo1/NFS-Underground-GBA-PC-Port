from pathlib import Path
p=Path('work/camera');h=(p/'live_hud_owned_view_candidate.h').read_text()
helper='''static int hud_visual_rows_equal(void){
 for(unsigned y=0;y<160;y++){
  const NFHudLayerRow*a=sky_hud_cached_rows+y,*b=owned_hud+y;
  if(b->refresh!=hud_refresh||b->row!=y||a->row!=y)return 0;
  if(memcmp((const uint8_t*)a+8,(const uint8_t*)b+8,sizeof(*a)-8))return 0;
 }
 return 1;
}
'''
marker='static int endpoint_hud(void){';assert h.count(marker)==1
h=h.replace(marker,helper+marker)
a='!memcmp(sky_hud_cached_rows,owned_hud,sizeof(owned_hud))';assert h.count(a)==1
h=h.replace(a,'hud_visual_rows_equal()')
(p/'live_hud_visual_reuse_candidate.h').write_text(h)
s=(p/'owned_gpu_segmented_4k_candidate.c').read_text();assert s.count('#include "live_hud_owned_view_candidate.h"')==1
s=s.replace('#include "live_hud_owned_view_candidate.h"','#include "live_hud_visual_reuse_candidate.h"')
s+='\n__declspec(dllexport) int nf_hud_visual_cache_stats(uint64_t*out){if(!out)return 0;out[0]=sky_hud_cache_hits;out[1]=sky_hud_cache_misses;return 1;}\n'
(p/'owned_gpu_segmented_4k_hud_reuse_candidate.c').write_text(s)

