from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_clip_packet_candidate.c').read_text();pos=s.index('static int source_packet_append')
code='''typedef struct{float config[8];int rect[8];unsigned sampling,blending;} SourceDrawState;
static SourceDrawState source_draw_states[4096];
static void source_geometry_state(SourceDrawState*out){
 const float config[8]={0,240,160,0,1,1,.5f,0};memcpy(out->config,config,32);memcpy(out->rect,source_clip_current,16);
 out->rect[4]=300;out->rect[5]=0;out->rect[6]=3240;out->rect[7]=2160;out->sampling=3;out->blending=0;
}
'''
s=s[:pos]+code+s[pos:];s=s.replace('memcpy(source_draw_clips[source_owned_draws],source_clip_current,16);','memcpy(source_draw_clips[source_owned_draws],source_clip_current,16);source_geometry_state(source_draw_states+source_owned_draws);')
s+='''
__declspec(dllexport) int nf_source_state_copy(void*out,size_t bytes){if(!source_packet_open||source_packet_owner!=GetCurrentThreadId()||!out||bytes!=(size_t)source_owned_draws*sizeof(SourceDrawState))return 1;memcpy(out,source_draw_states,bytes);return 0;}
'''
(p/'owned_gpu_source_draw_state_candidate.c').write_text(s)
s=(p/'test_source_clip_packet_candidate.py').read_text().replace('owned-gpu-source-clip-packet-candidate.dll','owned-gpu-source-draw-state-candidate.dll').replace('source-clip-packet-records.bin','source-draw-state-records.bin').replace('source-clip-packet-payload.bin','source-draw-state-payload.bin')
s=s.replace('  packet_checks.append(dict(','''  gpu.nf_source_state_copy.argtypes=[C.c_void_p,C.c_size_t];states=C.create_string_buffer(nd*72);assert gpu.nf_source_state_copy(states,len(states))==0;Path(f'work/camera/prototype-runs/source-owned-state-{index}.bin').write_bytes(states.raw)
  packet_checks.append(dict(state_sha256=hashlib.sha256(states.raw).hexdigest(),''')
(p/'test_source_draw_state_candidate.py').write_text(s)
