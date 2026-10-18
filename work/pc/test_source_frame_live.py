from pathlib import Path
import ctypes as C,os,hashlib,json,struct,threading,subprocess,sys
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-frame-tests';fixtures=base/'NFSUG-background-owner-api-fixtures';native=base/'NFSUG-android-background-jni-native-local'
if '--clean-child' not in sys.argv:
 env=os.environ.copy()
 for name in ('NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS'):env.pop(name,None)
 raise SystemExit(subprocess.call([sys.executable,__file__,'--clean-child'],env=env))
with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(native/'capture-host.dll'));adapter=C.CDLL(str(out/'source-frame.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def function(dll,name,args,ret=I):
 f=getattr(dll,name);f.argtypes=args;f.restype=ret;return f
op=function(core,'nfa_core_open',[C.c_char_p],P);close=function(core,'nfa_core_close',[P],None);load=function(core,'nfa_core_load_state',[P,P,S]);step=function(core,'nfa_core_step',[P,U]);pixels=function(core,'nfa_core_pixels',[P],P);timing=function(core,'nfa_core_timing',[P,C.POINTER(Q)]);audio=function(core,'nfa_core_read_audio',[P,P,S],S)
bind=function(adapter,'nf_pc_source_api_bind_owner',[C.POINTER(API)])
cap=function(adapter,'nf_pc_source_frame_capture',[C.POINTER(API),S],P);free=function(adapter,'nf_pc_source_frame_free',[P],None);meta=function(adapter,'nf_pc_source_frame_info',[P,C.POINTER(Q)]);component=function(adapter,'nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)])
def address(name):return C.cast(getattr(core,'nfa_core_'+name),P).value
def data(frame,i,kind):
 ptr=P();n=S();assert component(frame,i,kind,C.byref(ptr),C.byref(n));return C.string_at(ptr,n.value)
def section(raw,index):at,n=struct.unpack_from('<2Q',raw,64+16*index);return raw[at:at+n]
def sha(raw):return hashlib.sha256(raw).hexdigest()
selected={struct.unpack_from('<Q',p.read_bytes(),32)[0]:p for p in fixtures.glob('source-race-background-*.nrb')}
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert sha(rom.read_bytes())=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593' and sha(state)=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[address(name) for name in ('capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership')],0);assert bind(C.byref(api));pcm=(C.c_int16*8192)();sound=hashlib.sha256();audioframes=ready=checked=components=0;whole=split=0;peak=0;held=None;held_hashes={};wrong_thread=False
try:
 assert load(h,state,len(state));assert not cap(C.byref(api),64*1024*1024)
 for name in ('capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable'):assert function(core,'nfa_core_'+name,[P,I])(h,1),name
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1
   assert C.string_at(pixels(h),153600)==oracle.read(153600),('Original pixels',index)
   before=(Q*4)();assert timing(h,before) and tuple(before[:2])==(16777216,280896) and before[2]==initial[2]+index+1 and before[3]==index+1
   frame=cap(C.byref(api),64*1024*1024)
   after=(Q*4)();assert timing(h,after) and tuple(before)==tuple(after),'Capture advanced logic'
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    audioframes+=n;sound.update(C.string_at(pcm,n*4))
   if not frame:continue
   info=(Q*8)();assert meta(frame,info);ready+=1;whole+=info[2]==1;split+=info[2]==2;peak=max(peak,info[5]);assert info[1]==before[2]-1
   if held is None:
    held=frame
    for owner in range(info[4]):
     for kind in range(1,5):held_hashes[owner,kind]=sha(data(held,owner,kind))
    held_hashes[0,0]=sha(data(held,0,0));wrong=[]
    worker=threading.Thread(target=lambda:wrong.append(cap(C.byref(api),64*1024*1024)));worker.start();worker.join();assert wrong==[None];wrong_thread=True
   if info[1] in selected:
    path=selected[info[1]];original=(fixtures/path.name.removeprefix('source-')).read_bytes();assert data(frame,0,0)==original;source_nab=section(section(path.read_bytes(),0),0)
    for owner in range(info[4]):
     geometry=section(source_nab,owner);serial=struct.unpack_from('<I',geometry,16)[0];assert data(frame,owner,1)==geometry;components+=1
     for kind,extension in [(2,'nrh'),(3,'nwh'),(4,'nrp')]:assert data(frame,owner,kind)==(fixtures/('owner-'+str(serial)+'.'+extension)).read_bytes();components+=1
    checked+=1
   if frame!=held:free(frame)
 assert ready==590 and checked==9 and components==68 and whole and split,(ready,checked,components,whole,split)
 assert audioframes==443007 and sound.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert load(h,state,len(state)) and not cap(C.byref(api),64*1024*1024)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(80):assert step(h,1|(16 if index>=60 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
 assert function(core,'nfa_core_capture_enable',[P,I])(h,0) and not cap(C.byref(api),64*1024*1024)
finally:close(h)
assert held
for (owner,kind),digest in held_hashes.items():assert sha(data(held,owner,kind))==digest
free(held)
result=dict(result='PASS_PC_NORMAL_SOURCE_FRAME_LIVE_CORE',original_frames=600,post_reset_original_frames=80,original_clock_hz=16777216,cycles_per_step=280896,capture_never_steps_logic=True,audio_frames=audioframes,audio_sha256=sound.hexdigest(),complete_frames=ready,whole=whole,split=split,selected_snapshots=checked,source_components_host_identical=components,largest_requested_frame_bytes=peak,wrong_thread_rejected=wrong_thread,reset_disable_rejected=True,held_frame_immutable_after_core_close=True,diagnostic_setup_flags=False,scope='Windows core plus immutable complete source-frame collector; no GPU/gameplay presentation')
result['adapter_sha256']=hashlib.sha256((out/'source-frame.dll').read_bytes()).hexdigest()
result['source_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('source_frame.c','source_frame.h')}
result['test_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['core_dll_sha256']=hashlib.sha256((native/'capture-host.dll').read_bytes()).hexdigest()
(out/'live-core-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
