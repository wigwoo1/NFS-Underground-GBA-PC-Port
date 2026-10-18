from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_packet_sink_candidate.c').read_text();pos=s.index('static int source_packet_append')
code='''static uint64_t source_packet_identity[3];static int source_packet_open;
__declspec(dllexport) int nf_source_packets_begin(uint64_t epoch,uint64_t generation,uint64_t index){
 if(!epoch||!generation||source_packet_open)return 1;if(nf_source_packets_reset())return 1;
 source_packet_identity[0]=epoch;source_packet_identity[1]=generation;source_packet_identity[2]=index;source_packet_open=1;return 0;
}
__declspec(dllexport) int nf_source_packets_identity(uint64_t*out){if(!out||!source_packet_open||source_packet_owner!=GetCurrentThreadId())return 1;memcpy(out,source_packet_identity,24);return 0;}
__declspec(dllexport) int nf_source_packets_close(void){if(source_packet_owner&&source_packet_owner!=GetCurrentThreadId())return 1;source_packet_open=0;source_packet_owner=0;source_owned_used=source_owned_draws=source_owned_overflow=0;memset(source_packet_identity,0,24);return 0;}
'''
s=s[:pos]+code+s[pos:];s=s.replace('if(source_packet_owner!=GetCurrentThreadId()||source_owned_draws','if(!source_packet_open||source_packet_owner!=GetCurrentThreadId()||source_owned_draws')
# Close on GPU teardown, but verify function layout before inserting.
needle='__declspec(dllexport) int nf_owned_gpu_close(void){';assert needle in s
s=s.replace(needle,needle+'if(nf_source_packets_close())return 0;')
(p/'owned_gpu_source_packet_identity_candidate.c').write_text(s)
s=(p/'test_source_packet_sink_candidate.py').read_text().replace('owned-gpu-source-packet-sink-candidate.dll','owned-gpu-source-packet-identity-candidate.dll').replace('source-packet-sink-records.bin','source-packet-identity-records.bin').replace('source-packet-sink-payload.bin','source-packet-identity-payload.bin')
s=s.replace('  assert gpu.nf_source_packets_reset()==0','  gpu.nf_source_packets_begin.argtypes=[C.c_uint64]*3;gpu.nf_source_packets_identity.argtypes=[C.c_void_p]\n  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,1,index)==0;assert gpu.nf_source_packets_begin(1,1,index)==1\n  identity=(C.c_uint64*3)();assert gpu.nf_source_packets_identity(identity)==0 and list(identity)==[1,1,index]')
(p/'test_source_packet_identity_candidate.py').write_text(s)
