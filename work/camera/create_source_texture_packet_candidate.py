from pathlib import Path
p=Path('work/camera');h=(p/'owned_decoded_texture.h').read_text();h=h.replace('return preview_texture(w,h,t->rgba);','if(!source_texture_own(w,h,t->rgba))return 0;return preview_texture(w,h,t->rgba);').replace('return preview_texture(w,h,rgba);','if(!source_texture_own(w,h,rgba))return 0;return preview_texture(w,h,rgba);');(p/'owned_decoded_packet_texture_candidate.h').write_text(h)
s=(p/'owned_gpu_source_packet_identity_candidate.c').read_text().replace('#include "owned_decoded_texture.h"','static int source_texture_own(unsigned,unsigned,const uint8_t*);\n#include "owned_decoded_packet_texture_candidate.h"')
pos=s.index('static double source_owned_vertices')
code='''static uint8_t source_texture_bytes[16*1024*1024];static unsigned source_texture_records[64][4],source_texture_count,source_texture_used,source_texture_current,source_draw_textures[4096];
static int source_texture_own(unsigned w,unsigned h,const uint8_t*rgba){
 size_t n=(size_t)w*h*4;
 for(unsigned j=0;j<source_texture_count;j++)if(source_texture_records[j][0]==w&&source_texture_records[j][1]==h&&!memcmp(source_texture_bytes+source_texture_records[j][2],rgba,n)){source_texture_current=j+1;return 1;}
 if(source_texture_count>=64||n>sizeof(source_texture_bytes)-source_texture_used)return 0;
 unsigned*r=source_texture_records[source_texture_count];r[0]=w;r[1]=h;r[2]=source_texture_used;r[3]=(unsigned)n;memcpy(source_texture_bytes+source_texture_used,rgba,n);source_texture_used+=(unsigned)n;source_texture_current=++source_texture_count;return 1;
}
'''
s=s[:pos]+code+s[pos:]
s=s.replace('source_owned_used=source_owned_draws=source_owned_overflow=0;','source_owned_used=source_owned_draws=source_owned_overflow=0;source_texture_count=source_texture_used=source_texture_current=0;')
s=s.replace('memcpy(source_owned_vertices+source_owned_used,vertices,','source_draw_textures[source_owned_draws]=source_texture_current;memcpy(source_owned_vertices+source_owned_used,vertices,')
s+='''
__declspec(dllexport) int nf_source_texture_stats(unsigned*out){if(!out||!source_packet_open||source_packet_owner!=GetCurrentThreadId())return 1;out[0]=source_texture_count;out[1]=source_texture_used;return 0;}
__declspec(dllexport) int nf_source_texture_copy(void*rgba,size_t bytes,unsigned*records,size_t rbytes,unsigned*drawids,size_t dbytes){if(!source_packet_open||source_packet_owner!=GetCurrentThreadId()||!rgba||!records||!drawids||bytes!=source_texture_used||rbytes!=(size_t)source_texture_count*16||dbytes!=(size_t)source_owned_draws*4)return 1;memcpy(rgba,source_texture_bytes,bytes);memcpy(records,source_texture_records,rbytes);memcpy(drawids,source_draw_textures,dbytes);return 0;}
'''
(p/'owned_gpu_source_texture_packet_candidate.c').write_text(s)
s=(p/'test_source_packet_identity_candidate.py').read_text().replace('owned-gpu-source-packet-identity-candidate.dll','owned-gpu-source-texture-packet-candidate.dll').replace('source-packet-identity-records.bin','source-texture-packet-records.bin').replace('source-packet-identity-payload.bin','source-texture-packet-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  gpu.nf_source_texture_stats.argtypes=[C.c_void_p];gpu.nf_source_texture_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
  ts=(C.c_uint*2)();assert gpu.nf_source_texture_stats(ts)==0;nt,nb=ts;assert nt>0 and nb>0
  tb=C.create_string_buffer(nb);tr=(C.c_uint*(nt*4))();di=(C.c_uint*nd)();assert gpu.nf_source_texture_copy(tb,nb,tr,C.sizeof(tr),di,C.sizeof(di))==0
  assert all(1<=x<=nt for x in di);assert all(tr[j*4+3]==tr[j*4]*tr[j*4+1]*4 and tr[j*4+2]+tr[j*4+3]<=nb for j in range(nt))
  packet_checks.append(dict(texture_count=nt,texture_bytes=nb,texture_sha256=hashlib.sha256(tb.raw).hexdigest(),''')
(p/'test_source_texture_packet_candidate.py').write_text(s)
