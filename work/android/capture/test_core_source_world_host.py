"""Real core API replay: no host-only observer exports or capture environment gates."""
import ctypes as C,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
FLAGS=('NF_TEST_RACING_OWNED_CAPTURE','NF_CAPTURE_MODEL_VIEWS','NF_LIVE_ROAD_ATTRIBUTES')
if '--clean-child' not in sys.argv:
 env=os.environ.copy()
 for name in FLAGS:env.pop(name,None)
 raise SystemExit(subprocess.call([sys.executable,__file__,'--clean-child'],env=env))
assert not any(name in os.environ for name in FLAGS)
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');local=Path('C:/NFSUG-Workspace');out=local/'NFSUG-android-source-world-jni-local'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'))
P=C.c_void_p;U=C.c_uint32;Q=C.c_uint64;S=C.c_size_t

def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P)
enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);stats=api('capture_stats',[P,C.POINTER(Q)])
source_enable=api('capture_source_world_enable',[P,C.c_int]);source=api('capture_source_world',[P,Q,U,U,U,P,S],S)
legacy=api('capture_copy',[P,P,S],S);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S)
reference=json.loads((local/'NFSUG-android-shared-outcome-local/600-frame-audit/enabled-report.json').read_text());by_serial={r['serial']:r for r in reference['source_packets']}
state=(root/'work/integration-0.state').read_bytes();h=op(os.fsencode(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'));assert h
packets=[];seen=set();audio_hash=hashlib.sha256();audio_frames=0;pcm=(C.c_int16*8192)();guards=0;last_key=None
try:
 assert source_enable(h,1)==0
 assert load(h,state,len(state)) and enable(h,1) and layers(h,1) and source_enable(h,1)
 assert source_enable(h,1)==1 # Idempotent; must not discard current capture history.
 initial=(Q*4)();assert timing(h,initial)
 with (local/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(600):
   keys=1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0)
   assert step(h,keys)==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    assert n<=4096;audio_frames+=n;audio_hash.update(C.string_at(pcm,n*4))
   n=legacy(h,None,0)
   if not n:continue
   raw=C.create_string_buffer(n);assert legacy(h,raw,n)==n
   serial,begin,end=struct.unpack_from('<3I',raw.raw,16);info=(Q*8)();assert stats(h,info);key=(info[1],serial,begin,end)
   if key in seen:continue
   seen.add(key);size=source(h,*key,None,0);assert size,('Missing source scene',key)
   copied=C.create_string_buffer(size);assert source(h,*key,copied,size)==size
   digest=hashlib.sha256(copied.raw).hexdigest();ref=by_serial[serial];assert size==ref['bytes'] and digest==ref['sha256'],key
   packets.append(dict(identity=list(key),bytes=size,sha256=digest));last_key=key
   if serial==7:
    for bad in ((key[0]+1,*key[1:]),(key[0],key[1]+1,*key[2:]),(key[0],key[1],key[2]+1,key[3]),(key[0],key[1],key[2],key[3]+1)):
     marker=C.create_string_buffer(b'UNCHANGED');assert source(h,*bad,marker,len(marker))==0 and marker.raw==b'UNCHANGED\0';guards+=1
    marker=C.create_string_buffer(b'UNCHANGED');assert source(h,*key,marker,len(marker))==0 and marker.raw==b'UNCHANGED\0';guards+=1
 assert len(packets)==148 and len(seen)==148
 assert audio_frames==443007 and audio_hash.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert load(h,state,len(state)) and source(h,*last_key,None,0)==0
 info=(Q*8)();assert stats(h,info);assert info[1]!=last_key[0]
 reset_seen=set()
 with (local/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(64):
   assert step(h,1|(16 if 60<=i<120 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   n=legacy(h,None,0)
   if not n:continue
   raw=C.create_string_buffer(n);assert legacy(h,raw,n)==n;serial,begin,end=struct.unpack_from('<3I',raw.raw,16);assert stats(h,info);key=(info[1],serial,begin,end)
   if key in reset_seen:continue
   size=source(h,*key,None,0);assert size;buf=C.create_string_buffer(size);assert source(h,*key,buf,size)==size and hashlib.sha256(buf.raw).hexdigest()==by_serial[serial]['sha256'];reset_seen.add(key)
 assert len(reset_seen)==14
 assert source_enable(h,0) and source(h,*key,None,0)==0
 assert source_enable(h,1) and source(h,*key,None,0)==0 # Re-enable starts fresh; cannot borrow old history.
 assert enable(h,0) and source_enable(h,1)==0 and source(h,*key,None,0)==0
finally:close(h)
assert source(h,*last_key,None,0)==0 and source_enable(h,1)==0
report=dict(result='PASS_CORE_SOURCE_WORLD_NO_ENV_REPLAY_LIFECYCLE',original_frames=600,original_timing=True,audio_frames=audio_frames,audio_sha256=audio_hash.hexdigest(),source_packets=len(packets),all_packets_equal_shared_reference=True,wrong_owner_and_short_buffer_guards=guards,reset_replay_frames=64,reset_replay_packets=len(reset_seen),stale_epoch_rejected=True,disable_reenable_close_guards=True,test_environment_flags_required=False,source_packets_metadata=packets,android_runtime_tested=False,live_renderer_tested=False)
(out/'core-source-world-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_packets_metadata'},indent=2))
