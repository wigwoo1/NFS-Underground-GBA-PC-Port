from pathlib import Path
import ctypes as C,hashlib,json,os,struct
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-model-tests';refs=out/'references'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-model.dll'));core=C.CDLL(str(base/'NFSUG-android-background-jni-native-local/capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,name,args,ret=I):f=getattr(d,name);f.argtypes=args;f.restype=ret;return f
read=fn(d,'nf_pc_model_mesh_decode',[P,S,S],P);make=fn(d,'nf_pc_source_model_mesh',[P,U,U,S],P);count=fn(d,'nf_pc_source_model_count',[P,U],U);free=fn(d,'nf_pc_model_mesh_free',[P],None);info=fn(d,'nf_pc_model_mesh_info',[P,C.POINTER(Q)]);buffer=fn(d,'nf_pc_model_mesh_buffer',[P,U,C.POINTER(P),C.POINTER(S)]);plane=fn(d,'nf_pc_model_mesh_plane',[P,U,C.POINTER(C.c_float)])
cap=fn(d,'nf_pc_source_frame_capture',[C.POINTER(API),S],P);bind=fn(d,'nf_pc_source_api_bind_owner',[C.POINTER(API)]);release=fn(d,'nf_pc_source_frame_free',[P],None)
def blob(mesh,kind):p=P();n=S();assert buffer(mesh,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value)
rows={}
for line in (refs/'models.txt').read_text().splitlines():name,*values=line.split();rows[name]=list(map(int,values))
models=vertices=planes=0;malformed=0;peak=0;synthetic={}
def check(mesh,name,layout):
 global models,vertices,planes,peak
 expected=rows[name];meta=(Q*12)();assert info(mesh,meta);assert list(meta[:6])==expected[:6],(name,list(meta),expected)
 if layout:assert list(meta[7:11])==expected[6:10] and meta[11]==expected[10],('Layout',name,list(meta),expected)
 peak=max(peak,meta[6])
 for kind,suffix in enumerate(('vertices','camera','rgba','indices')):assert blob(mesh,kind)==(refs/(name+'.'+suffix)).read_bytes(),(name,suffix)
 actual=[]
 for triangle in range(meta[4]//3):
  p=(C.c_float*11)();assert plane(mesh,triangle,p);actual.append(bytes(p));planes+=1
 assert b''.join(actual)==(refs/(name+'.planes')).read_bytes(),('Texture planes',name)
 p=(C.c_float*11)(*[7]*11);assert not plane(mesh,meta[4]//3,p) and list(p)==[7]*11
 vertices+=meta[4];models+=1;return meta
for name in rows:
 raw=(refs/(name+'.model')).read_bytes();source=C.create_string_buffer(raw);mesh=read(source,len(raw),32*1024*1024);assert mesh,name
 try:
  meta=check(mesh,name,False);C.memset(source,0,len(raw));assert all(blob(mesh,kind)==(refs/(name+'.'+suffix)).read_bytes() for kind,suffix in enumerate(('vertices','camera','rgba','indices')));assert not read(raw,len(raw),meta[6]-1);exact=read(raw,len(raw),meta[6]);assert exact;free(exact)
  if name.startswith('synthetic-'):synthetic[name]=meta[4]
 finally:free(mesh)
raw=(refs/'synthetic-near.model').read_bytes()
for at in (0,4,8,12,16,20):
 bad=bytearray(raw);struct.pack_into('<I',bad,at,0);assert not read(bytes(bad),len(bad),32*1024*1024);malformed+=1
for at in (24,32,40,48,96,104,152,160,239):
 bad=bytearray(raw);struct.pack_into('<d',bad,at,float('nan'));assert not read(bytes(bad),len(bad),32*1024*1024);malformed+=1
for bad in (raw[:-1],raw+b'x',raw[:159]):assert not read(bad,len(bad),32*1024*1024);malformed+=1
bad=bytearray(raw);struct.pack_into('<H',bad,233,3);assert not read(bytes(bad),len(bad),32*1024*1024);malformed+=1
assert synthetic=={'synthetic-near':6,'synthetic-back':0,'synthetic-hidden':0},synthetic
# Normal live core frame path: source model extraction, ordering and bounds.
for name in ('NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS'):os.environ.pop(name,None)
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,C.POINTER(Q)]);layer=fn(core,'nfa_core_capture_layer_info',[P,C.POINTER(Q)]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S)
def address(name):return C.cast(getattr(core,'nfa_core_'+name),P).value
selected={int(name.split('-')[0]) for name in rows if not name.startswith('synthetic')};seen=set();live_models=0;held=None;held_hashes=[];state=(root/'work/integration-0.state').read_bytes();rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';assert hashlib.sha256(rom.read_bytes()).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[address(name) for name in ('capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership')],0);assert bind(C.byref(api));pcm=(C.c_int16*8192)()
try:
 assert load(h,state,len(state))
 for name in ('capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable'):assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1;display=(Q*5)()
   if not layer(h,display) or display[1] not in selected or display[1] in seen:continue
   frame=cap(C.byref(api),64*1024*1024);assert frame;refresh=display[1]
   try:
    owners={int(name.split('-')[1]) for name in rows if name.startswith(str(refresh)+'-')}
    for owner in sorted(owners):
     n=count(frame,owner);assert n==sum(name.startswith(str(refresh)+'-'+str(owner)+'-') for name in rows)
     for model in range(n):
      name=f'{refresh}-{owner}-{model}';mesh=make(frame,owner,model,32*1024*1024);assert mesh,name
      try:check(mesh,name,True);live_models+=1
      finally:
       if held is None:held=mesh;held_hashes=[hashlib.sha256(blob(mesh,k)).hexdigest() for k in range(4)]
       else:free(mesh)
    assert not make(frame,2,0,32*1024*1024) and not make(frame,0,99,32*1024*1024)
    after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick),'Model read advanced logic';seen.add(refresh)
   finally:release(frame)
   if seen==selected:break
finally:close(h)
assert len(seen)==9 and live_models==len(rows)-3 and held
assert [hashlib.sha256(blob(held,k)).hexdigest() for k in range(4)]==held_hashes;free(held)
result=dict(result='PASS_PC_SOURCE_MODEL_MESH',source_frames=9,reference_models=len(rows)-3,synthetic_models=3,live_source_models=live_models,model_comparisons=models,triangle_vertices_compared=vertices,texture_planes_compared=planes,malformed_rejected=malformed,synthetic_triangle_vertices=synthetic,maximum_requested_mesh_bytes=peak,source_frame_release_and_core_close_safe=True,original_prefix_frames=index+1,clock_hz=16777216,cycles_per_step=280896,reader_never_steps_logic=True,mesh_camera_rgba_indices_planes_byte_identical=True,source_draw_bounds_order_equal=True,dll_sha256=hashlib.sha256((out/'source-model.dll').read_bytes()).hexdigest(),core_sha256=hashlib.sha256((base/'NFSUG-android-background-jni-native-local/capture-host.dll').read_bytes()).hexdigest(),gpu_model_drawing=False,full_scene=False,full_scene_60fps=False)
result['source_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('source_frame.c','source_frame.h','model_mesh.c','model_mesh.h')}
result['test_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'model-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
