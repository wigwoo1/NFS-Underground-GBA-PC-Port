from pathlib import Path
p=Path('work/camera');h=(p/'live_hud_sky_candidate.h').read_text();needle=' if(ok){active(0x84c0);color=preview_texture'
assert needle in h;h=h.replace(needle,' if(ok&&!source_hud_planes_own(final_colors,metadata,text_colors,has_text))ok=0;\n'+needle);(p/'live_hud_packet_candidate.h').write_text(h)
s=(p/'owned_gpu_source_sky_packet_candidate.c').read_text();s=s.replace('static int source_packet_frozen;','static int source_hud_planes_own(const void*,const void*,const void*,int);static unsigned source_hud_valid,source_hud_text_enabled;static uint8_t source_hud_planes[3][153600];static int source_packet_frozen;')
s=s.replace('#include "live_hud_sky_candidate.h"','#include "live_hud_packet_candidate.h"').replace('source_sky_valid[0]=source_sky_valid[1]=0;','source_sky_valid[0]=source_sky_valid[1]=0;source_hud_valid=source_hud_text_enabled=0;')
s+='''
static int source_hud_planes_own(const void*color,const void*metadata,const void*text,int enabled){if(!source_texture_allowed()||!color||!metadata||!text)return 0;memcpy(source_hud_planes[0],color,153600);memcpy(source_hud_planes[1],metadata,153600);if(enabled)memcpy(source_hud_planes[2],text,153600);else memset(source_hud_planes[2],0,153600);source_hud_text_enabled=!!enabled;source_hud_valid=1;return 1;}
__declspec(dllexport) int nf_source_hud_planes_info(unsigned*out){if(!out||!source_packet_open||source_packet_owner!=GetCurrentThreadId())return 1;out[0]=source_hud_valid;out[1]=source_hud_text_enabled;return 0;}
__declspec(dllexport) int nf_source_hud_plane_copy(unsigned plane,void*out,size_t bytes){if(plane>2||!out||bytes!=153600||!source_packet_open||source_packet_owner!=GetCurrentThreadId()||!source_hud_valid)return 1;memcpy(out,source_hud_planes[plane],153600);return 0;}
'''
(p/'owned_gpu_source_hud_planes_candidate.c').write_text(s)
s=(p/'test_source_sky_packet_candidate.py').read_text().replace('owned-gpu-source-sky-packet-candidate.dll','owned-gpu-source-hud-planes-candidate.dll').replace('source-sky-packet-records.bin','source-hud-planes-records.bin').replace('source-sky-packet-payload.bin','source-hud-planes-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  gpu.nf_source_hud_planes_info.argtypes=[C.c_void_p];gpu.nf_source_hud_plane_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];hud_info=(C.c_uint*2)();assert gpu.nf_source_hud_planes_info(hud_info)==0 and hud_info[0]==1
  hud_hashes=[]
  for plane in range(3):
   hb=C.create_string_buffer(153600);assert gpu.nf_source_hud_plane_copy(plane,hb,len(hb))==0;hud_hashes.append(hashlib.sha256(hb.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-hud-{index}-{plane}.rgba').write_bytes(hb.raw)
  packet_checks.append(dict(hud_info=list(hud_info),hud_hashes=hud_hashes,''')
(p/'test_source_hud_planes_candidate.py').write_text(s)
