from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_packet_integration_candidate.c').read_text();pos=s.index('static int source_packet_gl')
code='''static double source_owned_vertices[65536][10];static unsigned source_owned_offsets[4097],source_owned_used,source_owned_draws,source_owned_overflow;static DWORD source_packet_owner;
__declspec(dllexport) int nf_source_packets_reset(void){if(source_packet_owner&&source_packet_owner!=GetCurrentThreadId())return 1;source_packet_owner=GetCurrentThreadId();source_owned_used=source_owned_draws=source_owned_overflow=0;source_owned_offsets[0]=0;return 0;}
__declspec(dllexport) int nf_source_packets_stats(unsigned*out){if(!out||source_packet_owner!=GetCurrentThreadId())return 1;out[0]=source_owned_used;out[1]=source_owned_draws;out[2]=source_owned_overflow;return 0;}
__declspec(dllexport) int nf_source_packets_copy(double*vertices,size_t bytes,unsigned*offsets,size_t offsetbytes){if(source_packet_owner!=GetCurrentThreadId()||!vertices||!offsets||bytes!=(size_t)source_owned_used*80||offsetbytes!=(size_t)(source_owned_draws+1)*4||source_owned_overflow)return 1;memcpy(vertices,source_owned_vertices,bytes);memcpy(offsets,source_owned_offsets,offsetbytes);return 0;}
static int source_packet_append(const double*vertices,unsigned count){if(source_packet_owner!=GetCurrentThreadId()||source_owned_draws>=4096||count>65536-source_owned_used){source_owned_overflow=1;return 0;}memcpy(source_owned_vertices+source_owned_used,vertices,(size_t)count*80);source_owned_used+=count;source_owned_offsets[++source_owned_draws]=source_owned_used;return 1;}
'''
s=s[:pos]+code+s[pos:];s=s.replace('glBegin(GL_TRIANGLES);for(unsigned j=0;j<written;j++)','if(!source_packet_append(output,written))return 0;glBegin(GL_TRIANGLES);for(unsigned j=0;j<written;j++)')
(p/'owned_gpu_source_packet_sink_candidate.c').write_text(s)
s=(p/'test_source_packet_integration_candidate.py').read_text().replace('owned-gpu-source-packet-integration-candidate.dll','owned-gpu-source-packet-sink-candidate.dll').replace('source-packet-integration-records.bin','source-packet-sink-records.bin').replace('source-packet-integration-payload.bin','source-packet-sink-payload.bin')
s=s.replace('checks=[];images=[]','packet_checks=[];checks=[];images=[];gpu.nf_source_packets_stats.argtypes=[C.c_void_p];gpu.nf_source_packets_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]')
s=s.replace(' for index,item in enumerate(expected):',' for index,item in enumerate(expected):\n  assert gpu.nf_source_packets_reset()==0')
s=s.replace('  checks.append(dict(','''  packet_stats=(C.c_uint*3)();assert gpu.nf_source_packets_stats(packet_stats)==0;nv,nd,overflow=packet_stats;assert nv>0 and nd>0 and overflow==0
  owned_vertices=C.create_string_buffer(nv*80);owned_offsets=(C.c_uint*(nd+1))();assert gpu.nf_source_packets_copy(owned_vertices,len(owned_vertices),owned_offsets,C.sizeof(owned_offsets))==0
  import struct,math
  assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<d',owned_vertices.raw));assert owned_offsets[0]==0 and owned_offsets[-1]==nv and all((owned_offsets[j+1]-owned_offsets[j])%3==0 for j in range(nd))
  packet_checks.append(dict(frame=index,vertices=nv,draws=nd,overflow=overflow,sha256=hashlib.sha256(owned_vertices.raw).hexdigest()));Path(f'work/camera/prototype-runs/source-owned-vertices-{index}.bin').write_bytes(owned_vertices.raw)
  checks.append(dict(''')
s=s.replace('result=dict(command_counts=','result=dict(source_packet_checks=packet_checks,command_counts=')
(p/'test_source_packet_sink_candidate.py').write_text(s)
