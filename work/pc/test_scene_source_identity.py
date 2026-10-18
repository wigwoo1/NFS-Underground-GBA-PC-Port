from pathlib import Path
import ctypes as C,os,struct,hashlib,json,threading
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-scene-source-identity-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'live-build-report.json').read_text());assert sha(out/'scene-source-identity.dll')==b['identity_dll_sha256'] and sha(out/'capture-host.dll')==b['core_sha256']
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(k,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'scene-source-identity.dll'));core=C.CDLL(str(out/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,n,args,r=I):f=getattr(lib,n);f.argtypes=args;f.restype=r;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(d,'nf_pc_source_api_bind_owner',[P]);capture=fn(d,'nf_pc_source_frame_capture',[P,S],P);frame_free=fn(d,'nf_pc_source_frame_free',[P],None);finfo=fn(d,'nf_pc_source_frame_info',[P,P]);owner=fn(d,'nf_pc_source_frame_owner',[P,U,P]);component=fn(d,'nf_pc_source_frame_component',[P,U,U,P,P]);prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);scene_free=fn(d,'nf_pc_scene_free',[P],None);sinfo=fn(d,'nf_pc_scene_info',[P,P]);command_info=fn(d,'nf_pc_scene_command_info',[P,U,P]);identity=fn(d,'nf_pc_scene_command_source',[P,U,P,P]);world_decode=fn(d,'nf_pc_world_decode',[P,S,S],P);world_free=fn(d,'nf_pc_world_free',[P],None);model_identity=fn(d,'nf_pc_world_model_identity',[P,U,P])
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));start=(Q*4)();assert timing(h,start)
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+n,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api))
pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;scenes=commands=models=worlds=guards=0;held=None;expected_held=None
def reject(scene,index,optr,iptr):
 global guards
 oq=(Q*5)(*[0xcccccccccccccccc]*5);iu=(U*5)(*[0xdddddddd]*5)
 assert not identity(scene,index,C.byref(oq) if optr else None,C.byref(iu) if iptr else None)
 assert list(oq)==[0xcccccccccccccccc]*5 and list(iu)==[0xdddddddd]*5;guards+=1
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(296):
   assert step(h,1|(16 if 60<=index<120 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==start[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   frame=capture(C.byref(api),64*1024*1024)
   if not frame:continue
   scene=None
   try:
    fi=(Q*8)();assert finfo(frame,fi);scene=prepare(frame,64*1024*1024);assert scene;si=(Q*8)();assert sinfo(scene,si);expected=[]
    for oi in range(fi[4]):
     key=(Q*5)();assert owner(frame,oi,key);p=P();n=S();assert component(frame,oi,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value)
     word=lambda at:struct.unpack_from('<I',packet,at)[0]
     ids=word(84);order=word(60);entries=word(order+4)
     wi=world_decode(packet,len(packet),64*1024*1024);assert wi
     try:
      world_count=word(word(48)+4)
      for j in range(entries):
       value=word(order+8+j*4);is_model=value>=0xfffffff0;number=0xffffffff-value if is_model else value;at=world_count+number if is_model else number
       original=struct.unpack_from('<5I',packet,ids+8+at*20)
       expected.append((oi,int(is_model),number,j,tuple(key),original))
       if is_model:
        actual=(U*5)();assert model_identity(wi,number,actual) and tuple(actual)==original;models+=1
       else:worlds+=1
      sentinel=(U*5)(*[0xa5a5a5a5]*5);assert not model_identity(wi,0xffffffff,sentinel) and list(sentinel)==[0xa5a5a5a5]*5;assert not model_identity(None,0,sentinel);assert not model_identity(wi,0,None);guards+=3
     finally:world_free(wi)
    assert len(expected)==si[3];captured=[]
    for j,e in enumerate(expected):
     ci=(Q*16)();oq=(Q*5)();iu=(U*5)();assert command_info(scene,j,ci) and identity(scene,j,oq,iu)
     assert (ci[0],ci[1],ci[2],ci[15])==e[:4] and tuple(oq)==e[4] and tuple(iu)==e[5]
     captured.append((tuple(oq),tuple(iu)))
    commands+=len(expected);scenes+=1
    reject(scene,si[3],True,True);reject(scene,0,False,True);reject(scene,0,True,False);reject(None,0,True,True)
    if held:scene_free(held)
    held=scene;scene=None;expected_held=captured
   finally:
    if scene:scene_free(scene)
    frame_free(frame)
finally:close(h)
assert held and scenes>=280 and commands==models+worlds
assert digest.hexdigest()==sha(base/'NFSUG-pc-present-lock-tests/candidate-delay.pcm')
errors=[]
def detached_reader():
 try:
  for j,e in enumerate(expected_held):
   oq=(Q*5)();iu=(U*5)();assert identity(held,j,oq,iu) and (tuple(oq),tuple(iu))==e
 except BaseException as exc:errors.append(repr(exc))
t=threading.Thread(target=detached_reader);t.start();t.join();assert not errors;scene_free(held)
assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_REAL_SCENE_COPIED_SOURCE_IDENTITIES',scenes=scenes,commands=commands,model_identities=models,world_identities=worlds,invalid_argument_guards=guards,identity_and_original_command_order_exact=True,owner_keys_exact=True,frame_and_core_destruction_and_new_thread_survival=True,original_frame_oracle_exact=True,pcm_sha256=digest.hexdigest(),pcm_frames=samples,core_sha256=b['core_sha256'],identity_dll_sha256=b['identity_dll_sha256'],source_sha256=b['source_sha256'],test_sha256=sha(Path(__file__)),protected_sha256=protected,full_scene_60fps=False,motion_interpolation_enabled=False)
(out/'identity-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','protected_sha256']},indent=2))
