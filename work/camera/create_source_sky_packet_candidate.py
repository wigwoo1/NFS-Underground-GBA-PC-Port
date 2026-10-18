from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_publish_candidate.c').read_text();s=s.replace('static int source_packet_frozen;','static int source_packet_frozen;static unsigned source_sky_valid[2];static uint8_t source_sky_rgba[2][153600];static double source_sky_alpha[2];static int source_sky_own(unsigned,const uint8_t*);')
s=s.replace('static GLuint sky_stream_texture(unsigned slot,const uint8_t*rgba){','static GLuint sky_stream_texture(unsigned slot,const uint8_t*rgba){if(!source_sky_own(slot,rgba))return 0;')
s=s.replace('source_packet_frozen=0;','source_packet_frozen=0;source_sky_valid[0]=source_sky_valid[1]=0;')
s+='''
static int source_sky_own(unsigned slot,const uint8_t*rgba){if(slot>1||!rgba||!source_texture_allowed())return 0;memcpy(source_sky_rgba[slot],rgba,153600);source_sky_valid[slot]=1;source_sky_alpha[slot]=slot?sky_weight:1;return 1;}
__declspec(dllexport) int nf_source_sky_info(unsigned*valid,double*weights){if(!valid||!weights||!source_packet_open||source_packet_owner!=GetCurrentThreadId())return 1;memcpy(valid,source_sky_valid,8);memcpy(weights,source_sky_alpha,16);return 0;}
__declspec(dllexport) int nf_source_sky_copy(unsigned slot,void*out,size_t bytes){if(slot>1||!out||bytes!=153600||!source_packet_open||source_packet_owner!=GetCurrentThreadId()||!source_sky_valid[slot])return 1;memcpy(out,source_sky_rgba[slot],153600);return 0;}
'''
(p/'owned_gpu_source_sky_packet_candidate.c').write_text(s)
s=(p/'test_source_publish_candidate.py').read_text().replace('owned-gpu-source-publish-candidate.dll','owned-gpu-source-sky-packet-candidate.dll').replace('source-publish-records.bin','source-sky-packet-records.bin').replace('source-publish-payload.bin','source-sky-packet-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  gpu.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p];gpu.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];sky_valid=(C.c_uint*2)();sky_weights=(C.c_double*2)();assert gpu.nf_source_sky_info(sky_valid,sky_weights)==0 and sky_valid[0]==1 and sky_weights[0]==1
  sky_hashes=[]
  for slot in range(2):
   if sky_valid[slot]:
    sky_bytes=C.create_string_buffer(153600);assert gpu.nf_source_sky_copy(slot,sky_bytes,len(sky_bytes))==0;sky_hashes.append(hashlib.sha256(sky_bytes.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-sky-{index}-{slot}.rgba').write_bytes(sky_bytes.raw)
    assert 0<=sky_weights[slot]<=1
  packet_checks.append(dict(sky_valid=list(sky_valid),sky_weights=list(sky_weights),sky_hashes=sky_hashes,''')
(p/'test_source_sky_packet_candidate.py').write_text(s)
