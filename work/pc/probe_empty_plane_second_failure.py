"""Capture one verified-route source frame; no renderer acceptance changes."""
from pathlib import Path
import ctypes as C,hashlib,json,os
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-empty-plane-second-failure';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reference=json.loads((base/'NFSUG-pc-traffic-rotation-draw-camera-route-tests/diverse-route-report.json').read_text());core=base/'NFSUG-pc-traffic-rotation-draw-camera-core/capture-host.dll';assert sha(core)==reference['core_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 d=C.CDLL(str(core));reader=C.CDLL(str(base/'NFSUG-pc-source-reader-direct-tests/source-reader.dll'));old=C.CDLL(str(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll'));diag=C.CDLL(str(base/'NFSUG-pc-empty-plane-failure-probe/source-scene-failure.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint;S=C.c_size_t;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,result=I):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';statepath=root/'work/integration-0.state';state=statepath.read_bytes();before={str(p):sha(p) for p in [rom,statepath]};h=fn(d,'nfa_core_open',[C.c_char_p],P)(os.fsencode(rom));assert h and fn(d,'nfa_core_load_state',[P,P,S])(h,state,len(state))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+n,[P,I])(h,1)
assert fn(d,'nfa_core_geometry_cache_enable',[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+n),P) for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert fn(reader,'nf_pc_source_api_bind_owner',[P])(C.byref(api))
r=fn(reader,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P)(C.byref(api),64*1024*1024,*[C.cast(getattr(d,'nfa_core_'+n),P) for n in ['capture_background_take','capture_owned_free','capture_source_world_take','capture_source_world_free']]);assert r
step=fn(d,'nfa_core_step',[P,U]);timing=fn(d,'nfa_core_timing',[P,P]);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;frame=None
try:
 for i,keys in enumerate(reference['input_keys'][:3800]):
  assert step(h,keys)==1;t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
  while True:
   n=audio(h,pcm,4096)
   if not n:break
   samples+=n;digest.update(C.string_at(pcm,n*4))
 frame=fn(reader,'nf_pc_source_reader_capture',[P,S],P)(r,64*1024*1024);assert frame;m=(Q*8)();assert fn(reader,'nf_pc_source_frame_info',[P,P])(frame,m)
 assert not fn(old,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024) and not fn(diag,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024)
 detail=(Q*32)();assert fn(diag,'nf_pc_scene_failure_detail',[P])(detail)
 witness=[];component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P])
 for owner in range(m[4]):
  identity=(Q*5)();assert owner_info(frame,owner,identity)
  for kind in range(5):
   if owner and not kind:continue
   ptr=P();n=S();assert component(frame,owner,kind,C.byref(ptr),C.byref(n));path=out/f'witness-owner{owner}-kind{kind}.bin';path.write_bytes(C.string_at(ptr,n.value));witness.append(dict(owner=owner,owner_info=list(identity),kind=kind,bytes=n.value,file=str(path),sha256=sha(path)))
 (out/'witness-components.json').write_text(json.dumps(witness,indent=2))
 report=dict(result='CAPTURED_SECOND_SCENE_PREPARE_FAILURE',logic_step=3800,frame_info=list(m),detail=list(detail),audio_frames=samples,audio_sha256=digest.hexdigest(),original_clocks_exact=True,core_sha256=sha(core),rom_state_sha256=before,script_sha256=sha(Path(__file__)),scope='One immutable source frame from the already verified core/input ledger. No new original-pixel/audio parity comparison in this focused replay.')
 (out/'second-failure-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:
 if frame:fn(reader,'nf_pc_source_frame_free',[P],None)(frame)
 fn(reader,'nf_pc_source_reader_close',[P],None)(r);fn(d,'nfa_core_close',[P],None)(h)
assert before=={str(p):sha(p) for p in [rom,statepath]}
