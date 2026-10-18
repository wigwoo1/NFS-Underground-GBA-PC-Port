"""Original-data and lifecycle regression on the current Windows capture build."""
from pathlib import Path
import ctypes as C,hashlib,json,os,struct
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');candidate=base/'NFSUG-Android-Context-Refresh-20261017';out=candidate/'host600-results';out.mkdir(exist_ok=True)
native=json.loads((candidate/'native/capture-jni-build-report.json').read_text());assert native['visibility_capacity']==64
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(candidate/'native/capture-host.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t
def api(name,args,ret=C.c_int):
 f=getattr(dll,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pause=api('pause',[P,C.c_int]);timing=api('timing',[P,C.POINTER(Q)]);pixels=api('pixels',[P],P);audio=api('read_audio',[P,P,S],S)
enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);world=api('capture_source_world_enable',[P,C.c_int]);walls=api('capture_wall_history_enable',[P,C.c_int]);sky=api('capture_sky_enable',[P,C.c_int]);stats=api('capture_stats',[P,C.POINTER(Q)]);bg=api('capture_background_scene',[P,Q,U,P,S],S);info=api('capture_layer_info',[P,C.POINTER(Q)])
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state_path=root/'work/integration-0.state';state=state_path.read_bytes();state_buf=C.create_string_buffer(state);keys=json.loads((base/'NFSUG-Android-Native-Wide-20261017/route-results/input-keys.json').read_text())[:600]
baseline=[];pcm=(C.c_int16*8192)();runs=[]
for captured in [False,True]:
 h=op(os.fsencode(rom));assert h;frames=hashlib.sha256();sound=hashlib.sha256();samples=0;missing=[];scene518=None
 try:
  assert load(h,state_buf,len(state)) and pause(h,0)
  if captured:assert enable(h,1) and layers(h,1) and world(h,1) and walls(h,1) and sky(h,1)
  initial=(Q*4)();assert timing(h,initial)
  for i,key in enumerate(keys,1):
   assert step(h,key)==1;t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i and t[3]==i
   digest=hashlib.sha256(C.string_at(pixels(h),153600)).digest();frames.update(digest)
   if captured:assert digest==baseline[i-1],('original-pixels',i)
   else:baseline.append(digest)
   n=audio(h,pcm,4096);assert n<=4096;sound.update(C.string_at(pcm,n*4));samples+=n
   if captured:
    layer=(Q*5)();assert info(h,layer);size=bg(h,layer[0],layer[1],None,0)
    if not size:missing.append(i)
    if i==518:
     assert size;buffer=C.create_string_buffer(size);assert bg(h,layer[0],layer[1],buffer,size)==size;scene518=dict(bytes=size,sha256=hashlib.sha256(buffer.raw).hexdigest(),layer_info=list(layer))
  if captured:
   assert missing==list(range(1,11));assert samples==runs[0]['audio_frames'] and sound.hexdigest()==runs[0]['audio_sha256']
   before=(Q*4)();assert timing(h,before) and pause(h,1)
   for _ in range(10):
    after=(Q*4)();assert step(h,1)==2 and timing(h,after) and list(after)==list(before)
   assert pause(h,0);before_stats=(Q*8)();assert stats(h,before_stats);old_epoch=before_stats[1]
   assert load(h,state_buf,len(state));reset=(Q*8)();assert stats(h,reset) and reset[1]>old_epoch
   assert step(h,keys[0])==1;layer=(Q*5)();assert info(h,layer)
   assert not bg(h,old_epoch,12359,None,0),'stale epoch returned scene'
   assert enable(h,0) and load(h,state_buf,len(state)) and pause(h,0)
   for i,key in enumerate(keys[:16]):
    assert step(h,key)==1 and hashlib.sha256(C.string_at(pixels(h),153600)).digest()==baseline[i]
  runs.append(dict(capture=captured,steps=600,original_frame_hash_chain=frames.hexdigest(),audio_frames=samples,audio_sha256=sound.hexdigest(),missing_background_steps=missing,scene518=scene518))
 finally:close(h)
assert runs[0]['original_frame_hash_chain']==runs[1]['original_frame_hash_chain'] and runs[1]['scene518']['sha256']=='4eb0f9b51e71c368aeff2955f1857689905cd863425bdf27dc004ea183a5f221'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(result='VERIFIED_WINDOWS_HOST600_ORIGINAL_DATA_CONTEXT_RECOVERY_AND_LIFECYCLE',runs=runs,original_pixels_pcm_clocks_exact=True,recovered_scene518_matches_android_original_background=True,pause_reset_stale_epoch_detach=True,host_dll_sha256=sha(candidate/'native/capture-host.dll'),helper_sha256=sha(root/'work/camera/model_context_refresh.h'),header_sha256=sha(root/'work/camera/live_visibility.h'),test_sha256=sha(Path(__file__)),limits='Windows borrowed-core capture/source regression, not the PC live renderer/audio device, GPU presentation, full race or smooth60.')
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
