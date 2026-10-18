from pathlib import Path
p=Path('work/camera');h=(p/'live_hud_visual_reuse_candidate.h').read_text();a=h.index('static int hud_visual_rows_equal');b=h.index('static int endpoint_hud',a)
s='#include <stdint.h>\n#include <string.h>\n#include "layer_snapshot.h"\nstatic NFHudLayerRow sky_hud_cached_rows[160];static const NFHudLayerRow*owned_hud;static uint32_t hud_refresh;\n'+h[a:b]
s+='__declspec(dllexport) int nf_test_hud_equal(const void*a,const void*b,uint32_t refresh){if(!a||!b)return 0;memcpy(sky_hud_cached_rows,a,sizeof(sky_hud_cached_rows));owned_hud=b;hud_refresh=refresh;return hud_visual_rows_equal();}\n__declspec(dllexport) unsigned nf_test_hud_row_size(void){return sizeof(NFHudLayerRow);}\n'
(p/'hud_visual_equal_component.c').write_text(s)
