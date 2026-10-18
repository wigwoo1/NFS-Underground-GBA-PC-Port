from pathlib import Path
p=Path('work/camera');h=(p/'live_hud_packet_candidate.h').read_text();needle='glScissor(0,2160-bottom,3840,bottom-top);';assert needle in h;h=h.replace(needle,'if(!source_hud_batch_own(bd,blend,alpha,brightness,priority,top,bottom)){ok=0;break;}'+needle);(p/'live_hud_batch_packet_candidate.h').write_text(h)
s=(p/'owned_gpu_source_hud_planes_candidate.c').read_text().replace('#include "live_hud_packet_candidate.h"','#include "live_hud_batch_packet_candidate.h"');s=s.replace('static int source_hud_planes_own(','static int source_hud_batch_own(unsigned,unsigned,unsigned,unsigned,unsigned,int,int);static int source_hud_planes_own(',1)
pos=s.index('static unsigned source_hud_valid');s=s[:pos]+'static unsigned source_hud_batch_count;static uint8_t source_hud_batches[160][112];'+s[pos:];s=s.replace('source_hud_valid=source_hud_text_enabled=0;','source_hud_valid=source_hud_text_enabled=0;source_hud_batch_count=0;')
s+='''
static int source_hud_batch_own(unsigned bd,unsigned blend,unsigned alpha,unsigned brightness,unsigned priority,int top,int bottom){
 if(!source_texture_allowed()||source_hud_batch_count>=160||top<0||bottom<top||bottom>2160)return 0;
 unsigned ea=alpha&31,eb=(alpha>>8)&31,ey=brightness&31;
 float f[20]={((bd&31)<<3)|((bd&31)>>2),((bd>>5&31)<<3)|((bd>>5&31)>>2),((bd>>10&31)<<3)|((bd>>10&31)>>2),1,(blend>>6)&3,0,0,priority,!!(blend&16),!!(blend&4),!!(blend&32),0,!!(blend&4096),!!(blend&1024),!!(blend&8192),0,ea>16?16:ea,eb>16?16:eb,ey>16?16:ey,0};
 uint8_t*r=source_hud_batches[source_hud_batch_count++];memset(r,0,112);memcpy(r,f,80);int enabled=source_hud_text_enabled;memcpy(r+80,&enabled,4);int rect[4]={0,top,3840,bottom};memcpy(r+96,rect,16);return 1;
}
__declspec(dllexport) int nf_source_hud_batches_count(void){if(!source_packet_open||source_packet_owner!=GetCurrentThreadId())return -1;return source_hud_batch_count;}
__declspec(dllexport) int nf_source_hud_batches_copy(void*out,size_t bytes){if(!out||!source_packet_open||source_packet_owner!=GetCurrentThreadId()||bytes!=(size_t)source_hud_batch_count*112)return 1;memcpy(out,source_hud_batches,bytes);return 0;}
'''
(p/'owned_gpu_source_hud_batches_candidate.c').write_text(s)
s=(p/'test_source_hud_planes_candidate.py').read_text().replace('owned-gpu-source-hud-planes-candidate.dll','owned-gpu-source-hud-batches-candidate.dll').replace('source-hud-planes-records.bin','source-hud-batches-records.bin').replace('source-hud-planes-payload.bin','source-hud-batches-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  count=gpu.nf_source_hud_batches_count();assert 0<count<=160;gpu.nf_source_hud_batches_copy.argtypes=[C.c_void_p,C.c_size_t];batch=C.create_string_buffer(count*112);assert gpu.nf_source_hud_batches_copy(batch,len(batch))==0;Path(f'work/camera/prototype-runs/source-owned-hud-batches-{index}.bin').write_bytes(batch.raw)
  packet_checks.append(dict(hud_batches=count,hud_batch_sha256=hashlib.sha256(batch.raw).hexdigest(),''')
(p/'test_source_hud_batches_candidate.py').write_text(s)
