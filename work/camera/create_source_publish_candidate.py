from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_draw_state_candidate.c').read_text();s=s.replace('static int source_texture_own(unsigned,unsigned,const uint8_t*);','static int source_texture_own(unsigned,unsigned,const uint8_t*);static int source_texture_allowed(void);static int source_packet_frozen;')
s=s.replace('static int source_texture_own(unsigned w,unsigned h,const uint8_t*rgba){','static int source_texture_own(unsigned w,unsigned h,const uint8_t*rgba){if(!source_texture_allowed())return 0;')
s=s.replace('source_texture_count=source_texture_used=source_texture_current=0;source_clip_valid=0;','source_texture_count=source_texture_used=source_texture_current=0;source_clip_valid=0;source_packet_frozen=0;')
s=s.replace('if(!source_packet_open||source_packet_owner!=GetCurrentThreadId()||source_owned_draws','if(source_packet_frozen||!source_packet_open||source_packet_owner!=GetCurrentThreadId()||source_owned_draws')
s+='''
static int source_texture_allowed(void){return source_packet_open&&!source_packet_frozen&&source_packet_owner==GetCurrentThreadId();}
__declspec(dllexport) int nf_source_packets_publish(uint64_t*out){
 if(!out||!source_packet_open||source_packet_frozen||source_packet_owner!=GetCurrentThreadId()||source_owned_overflow||!source_owned_draws||!source_texture_count)return 1;
 for(unsigned j=0;j<source_owned_draws;j++)if(!source_draw_textures[j]||source_draw_textures[j]>source_texture_count)return 1;
 source_packet_frozen=1;memcpy(out,source_packet_identity,24);out[3]=source_owned_used;out[4]=source_owned_draws;out[5]=source_texture_count;out[6]=source_texture_used;return 0;
}
'''
(p/'owned_gpu_source_publish_candidate.c').write_text(s)
s=(p/'test_source_draw_state_candidate.py').read_text().replace('owned-gpu-source-draw-state-candidate.dll','owned-gpu-source-publish-candidate.dll').replace('source-draw-state-records.bin','source-publish-records.bin').replace('source-draw-state-payload.bin','source-publish-payload.bin')
s=s.replace('  packet_stats=(C.c_uint*3)();','  gpu.nf_source_packets_publish.argtypes=[C.c_void_p];publication=(C.c_uint64*7)();assert gpu.nf_source_packets_publish(publication)==0 and list(publication[:3])==[1,1,index];assert gpu.nf_source_packets_publish(publication)==1\n  packet_stats=(C.c_uint*3)();')
s=s.replace('  checks.append(dict(','  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,2,index)==0\n  checks.append(dict(')
(p/'test_source_publish_candidate.py').write_text(s)
