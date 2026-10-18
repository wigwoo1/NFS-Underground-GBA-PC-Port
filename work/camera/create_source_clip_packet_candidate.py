from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_texture_packet_candidate.c').read_text();pos=s.index('static uint8_t source_texture_bytes')
s=s[:pos]+'static int source_clip_current[4],source_draw_clips[4096][4];static int source_clip_valid;\n'+s[pos:]
s=s.replace('source_texture_count=source_texture_used=source_texture_current=0;','source_texture_count=source_texture_used=source_texture_current=0;source_clip_valid=0;')
s=s.replace('source_draw_textures[source_owned_draws]=source_texture_current;','if(!source_clip_valid)return 0;memcpy(source_draw_clips[source_owned_draws],source_clip_current,16);source_draw_textures[source_owned_draws]=source_texture_current;')
s=s.replace('glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1-x0,y1-y0);return 1;','source_clip_current[0]=x0;source_clip_current[1]=2160-y1;source_clip_current[2]=x1;source_clip_current[3]=2160-y0;source_clip_valid=1;glEnable(GL_SCISSOR_TEST);glScissor(x0,y0,x1-x0,y1-y0);return 1;')
# Wall may set scissor directly: inspect after generation; no fabricated default.
s+='''
__declspec(dllexport) int nf_source_clip_copy(int*out,size_t bytes){if(!source_packet_open||source_packet_owner!=GetCurrentThreadId()||!out||bytes!=(size_t)source_owned_draws*16)return 1;memcpy(out,source_draw_clips,bytes);return 0;}
'''
(p/'owned_gpu_source_clip_packet_candidate.c').write_text(s)
s=(p/'test_source_texture_packet_candidate.py').read_text().replace('owned-gpu-source-texture-packet-candidate.dll','owned-gpu-source-clip-packet-candidate.dll').replace('source-texture-packet-records.bin','source-clip-packet-records.bin').replace('source-texture-packet-payload.bin','source-clip-packet-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  gpu.nf_source_clip_copy.argtypes=[C.c_void_p,C.c_size_t];clips=(C.c_int*(nd*4))();assert gpu.nf_source_clip_copy(clips,C.sizeof(clips))==0
  assert all(0<=clips[j*4]<=clips[j*4+2]<=3840 and 0<=clips[j*4+1]<=clips[j*4+3]<=2160 for j in range(nd))
  packet_checks.append(dict(clip_sha256=hashlib.sha256(bytes(clips)).hexdigest(),''')
(p/'test_source_clip_packet_candidate.py').write_text(s)
