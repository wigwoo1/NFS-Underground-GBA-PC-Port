from pathlib import Path
import ctypes as C,os,struct,io,json,hashlib
import test_world_mesh as component
from test_world_mesh import d,fn,P,S,U,Q,I,blob,make,free,plane,info
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-mesh-tests'
with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(base/'NFSUG-android-background-jni-native-local/capture-host.dll'))
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def cf(n,args,r=I):f=getattr(core,'nfa_core_'+n);f.argtypes=args;f.restype=r;return f
op=cf('open',[C.c_char_p],P);close=cf('close',[P],None);load=cf('load_state',[P,P,S]);step=cf('step',[P,U]);pixels=cf('pixels',[P],P);timing=cf('timing',[P,P]);audio=cf('read_audio',[P,P,S],S);layer=cf('capture_layer_info',[P,P]);bind=fn('nf_pc_source_api_bind_owner',[P]);capture=fn('nf_pc_source_frame_capture',[P,S],P);release=fn('nf_pc_source_frame_free',[P],None);read_world=fn('nf_pc_source_world',[P,U,S],P);world_free=fn('nf_pc_world_free',[P],None)
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert hashlib.sha256(rom.read_bytes()).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';assert hashlib.sha256(state).hexdigest()=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));selected={int(p.stem.split('-')[0]) for p in (out/'inputs').glob('*.nsp') if not p.name.startswith('synthetic')};seen=set();owners=surfaces=vertices=planes=0;held=None;held_buffers=None;pcm=(C.c_int16*8192)()
try:
 assert load(h,state,len(state))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert cf(name,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1;display=(Q*5)()
   if not layer(h,display) or display[1] not in selected or display[1] in seen:continue
   refresh=display[1];frame=capture(C.byref(api),64*1024*1024);assert frame
   try:
    for path in sorted((out/'references').glob(str(refresh)+'-*.mesh')):
     owner=int(path.stem.split('-')[1]);world=read_world(frame,owner,64*1024*1024);assert world;owners+=1;stream=io.BytesIO(path.read_bytes())
     def integer():return struct.unpack('>I',stream.read(4))[0]
     try:
      count=integer()
      for i in range(count):
       affine=integer();camera_mode=integer();nc=integer();camera=stream.read(nc*8);nf=integer();meshbytes=stream.read(nf*4);nt=integer();expected_planes=stream.read(nt*44);mesh=make(world,i,32*1024*1024);assert mesh
       try:
        meta=(Q*16)();assert info(mesh,meta) and meta[12]*5==nf and meta[13]==affine and meta[14]==camera_mode;assert blob(mesh,0)==meshbytes and blob(mesh,1)==camera;actual=[]
        for t in range(nt):p=(C.c_float*11)();assert plane(mesh,t,p);actual.append(bytes(p))
        assert b''.join(actual)==expected_planes;surfaces+=1;vertices+=nf//5;planes+=nt
       finally:
        if held:free(held)
        held=mesh;held_buffers=[meshbytes,camera]
      assert not stream.read()
     finally:world_free(world)
    after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick),'World projection advanced logic';seen.add(refresh)
   finally:release(frame)
   if seen==selected:break
finally:close(h)
assert len(seen)==9 and owners==17 and surfaces==388 and vertices==2943 and planes==981;assert [blob(held,k) for k in range(2)]==held_buffers;free(held)
r=dict(result='PASS_PC_WORLD_MESH_NORMAL_CORE',source_frames=9,owners=owners,surfaces=surfaces,triangle_vertices=vertices,texture_planes=planes,original_prefix_frames=index+1,original_pixels_exact=True,clock_hz=16777216,cycles_per_step=280896,projection_never_steps_logic=True,mesh_survives_world_frame_and_core_free=True,core_sha256=hashlib.sha256((base/'NFSUG-android-background-jni-native-local/capture-host.dll').read_bytes()).hexdigest(),dll_sha256=hashlib.sha256((out/'world-mesh.dll').read_bytes()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),gpu_world_drawing=False,full_scene=False,full_scene_60fps=False)
(out/'world-mesh-live-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
