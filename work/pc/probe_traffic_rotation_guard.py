from pathlib import Path
import ctypes as C,hashlib,json,os
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-rotation-guard-core'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();build=json.loads((out/'traffic-rotation-guard-build-report.json').read_text());assert build['core_sha256']==sha(out/'capture-host.dll')
for n,h in build['maintained_source_sha256'].items():assert sha(source/n)==h,n
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint32;Q=C.c_uint64

def fn(n,args,result=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);step=fn('nfa_core_step',[P,U]);timing=fn('nfa_core_timing',[P,P]);audio=fn('nfa_core_read_audio',[P,P,S],S);detail=fn('nfa_core_capture_traffic_guard_detail',[P,P,S])
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';statepath=root/'work/integration-0.state';state=statepath.read_bytes();before={str(p):sha(p) for p in [rom,statepath]};h=op(os.fsencode(rom));assert h and load(h,state,len(state))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn('nfa_core_'+n,[P,C.c_int])(h,1)
initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0
try:
 for i in range(3550):
  phase=i%1200;assert step(h,1|(32 if 180<=phase<500 else 16 if 500<=phase<720 else 0))
  tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+i+1 and tick[3]==i+1
  while True:
   n=audio(h,pcm,4096)
   if not n:break
   samples+=n;digest.update(C.string_at(pcm,n*4))
 result=(U*128)(*([0xdeadbeef]*128));assert not detail(h,result,127) and all(v==0xdeadbeef for v in result)
 assert detail(h,result,128) and tuple(result[:3])==(0x3147544e,1,128)
 report=dict(result='FROZEN_TRAFFIC_GUARD_REJECTION',steps=3550,detail=list(result),audio_frames=samples,audio_sha256=digest.hexdigest(),clocks_exact=True,short_buffer_atomic=True,core_sha256=sha(out/'capture-host.dll'),script_sha256=sha(Path(__file__)),rom_state_sha256=before,full_scene_60fps=False)
 (out/'traffic-guard-probe-report.json').write_text(json.dumps(report,indent=2));print('HEADER',list(result[:20]));print('CAMERA_DIFFERENCES',[(i,result[32+i],result[48+i]) for i in range(12) if result[32+i]!=result[48+i]]);print('MODEL_DIFFERENCES',[(i,result[64+i],result[80+i]) for i in range(9) if result[64+i]!=result[80+i]])
finally:close(h)
assert before=={str(p):sha(p) for p in [rom,statepath]}
