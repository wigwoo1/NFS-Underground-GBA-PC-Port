from pathlib import Path
import ctypes as C,os,json,hashlib
import test_source_world as component
from test_source_world import d,fn,P,S,U,I,Q,check,digest,free
root=Path(__file__).parent.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-tests';refs=out/'references'
with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(base/'NFSUG-android-background-jni-native-local/capture-host.dll'))
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def cf(name,args,r=I):f=getattr(core,'nfa_core_'+name);f.argtypes=args;f.restype=r;return f
op=cf('open',[C.c_char_p],P);close=cf('close',[P],None);load=cf('load_state',[P,P,S]);step=cf('step',[P,U]);pixels=cf('pixels',[P],P);timing=cf('timing',[P,C.POINTER(Q)]);audio=cf('read_audio',[P,P,S],S);layer=cf('capture_layer_info',[P,C.POINTER(Q)])
bind=fn('nf_pc_source_api_bind_owner',[C.POINTER(API)]);capture=fn('nf_pc_source_frame_capture',[C.POINTER(API),S],P);release=fn('nf_pc_source_frame_free',[P],None);make=fn('nf_pc_source_world',[P,U,S],P)
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert hashlib.sha256(rom.read_bytes()).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';assert hashlib.sha256(state).hexdigest()=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));pcm=(C.c_int16*8192)();selected={int(p.stem.split('-')[0]) for p in refs.glob('*.nsp') if not p.name.startswith('synthetic')};seen=set();held=None;held_digest=None;owners=0;surfaces_before=component.surfaces
try:
 assert load(h,state,len(state))
 for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert cf(n,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   before=(Q*4)();assert timing(h,before) and tuple(before[:2])==(16777216,280896) and before[2]==initial[2]+index+1 and before[3]==index+1;display=(Q*5)()
   if not layer(h,display) or display[1] not in selected or display[1] in seen:continue
   refresh=display[1];frame=capture(C.byref(api),64*1024*1024);assert frame
   try:
    files=sorted(refs.glob(str(refresh)+'-*.reference'))
    for reference in files:
     owner=int(reference.stem.split('-')[1]);world=make(frame,owner,64*1024*1024);assert world
     try:check(world,reference);owners+=1
     finally:
      if held is None:held=world;held_digest=digest(held)
      else:free(world)
    assert not make(frame,2,64*1024*1024);after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(before),'World decoding advanced logic';seen.add(refresh)
   finally:release(frame)
   if seen==selected:break
finally:close(h)
assert len(seen)==9 and owners==17 and component.surfaces-surfaces_before==388;assert digest(held)==held_digest;free(held)
r=dict(result='PASS_PC_WORLD_NORMAL_CORE',source_frames=9,owners=owners,surfaces=388,original_prefix_frames=index+1,original_pixels_exact=True,clock_hz=16777216,cycles_per_step=280896,decoder_never_steps_logic=True,world_survives_frame_release_and_core_close=True,core_sha256=hashlib.sha256((base/'NFSUG-android-background-jni-native-local/capture-host.dll').read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/'source-world.dll').read_bytes()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gpu_world_drawing=False,full_scene=False,full_scene_60fps=False)
(out/'world-live-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
