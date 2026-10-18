from pathlib import Path
import ctypes as C,hashlib,json,os,struct,threading
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-owned-pose-timing-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();build=json.loads((out/'live-build-report.json').read_text())
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'timed-scenes.dll'));core=C.CDLL(str(out/'timing-core.dll'))
assert sha(out/'timed-scenes.dll')==build['identity_dll_sha256'] and sha(out/'timing-core.dll')==build['timing_core_sha256']
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,r=I):f=getattr(lib,name);f.argtypes=args;f.restype=r;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);provider=fn(core,'nfa_core_capture_pose_timing',[P,Q,U,U,U,P,S],S)
capture=fn(d,'nf_pc_source_frame_capture_timed',[P,S,P],P);plain=fn(d,'nf_pc_source_frame_capture',[P,S],P);take=fn(d,'nf_pc_source_frame_capture_take_sources_timed',[P,S,P,P,P,P,P],P);frame_free=fn(d,'nf_pc_source_frame_free',[P],None);finfo=fn(d,'nf_pc_source_frame_info',[P,P]);fowner=fn(d,'nf_pc_source_frame_owner',[P,U,P]);component=fn(d,'nf_pc_source_frame_component',[P,U,U,P,P]);ftiming=fn(d,'nf_pc_source_frame_pose_timing',[P,U,P,P]);bind=fn(d,'nf_pc_source_api_bind_owner',[P]);prepare=fn(d,'nf_pc_scene_prepare_motion',[P,S],P);normal_prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);scene_free=fn(d,'nf_pc_scene_free',[P],None);sinfo=fn(d,'nf_pc_scene_info',[P,P]);stiming=fn(d,'nf_pc_scene_motion_timing',[P,U,P,P]);alpha=fn(d,'nf_pc_scene_pose_alpha',[P,U,P,U,C.c_double,P]);gpu_open=fn(d,'nf_pc_scene_gpu_open',[],P);gpu_close=fn(d,'nf_pc_scene_gpu_close',[P],None);gpu_draw=fn(d,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S])
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def reject_view(f,obj,owner):
 p=P(0x1234);n=S(0x5678);assert not f(obj,owner,C.byref(p),C.byref(n)) and p.value==0x1234 and n.value==0x5678
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));ptr=C.cast(provider,P);maximum=64*1024*1024
from collections import Counter
counts=Counter();previous=None;detached=None;retained_frame=None;g=None;pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;start=(Q*4)();assert timing(h,start);baseline=json.loads((base/'NFSUG-pc-pose-capture-timing-tests/baseline-route.json').read_text())['source_rows']
READ=C.CFUNCTYPE(S,P,Q,U,U,U,P,S)
def metadata(key):
 raw=C.create_string_buffer(184);assert provider(h,*key[:4],None,0)==184 and provider(h,*key[:4],raw,184)==184;return raw.raw
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600);t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==start[2]+index+1 and t[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   frame=capture(C.byref(api),maximum,ptr)
   if not frame:assert baseline[index] is None;continue
   ordinary=plain(C.byref(api),maximum);assert ordinary;fi=(Q*8)();oi=(Q*8)();assert finfo(frame,fi) and finfo(ordinary,oi) and fi[5]==oi[5]+184*fi[4]
   scene=prepare(frame,maximum);un_scene=prepare(ordinary,maximum);assert scene and un_scene;si=(Q*8)();ui=(Q*8)();assert sinfo(scene,si) and sinfo(un_scene,ui) and si[6]==ui[6]+184*fi[4];rows=[];times=[]
   for role in range(fi[4]):
    key=(Q*5)();assert fowner(frame,role,key);raw=metadata(list(key));assert blob(ftiming,frame,role)==blob(stiming,scene,role)==raw;times.append(struct.unpack_from('<16Q',raw));reject_view(ftiming,ordinary,role);reject_view(stiming,un_scene,role)
    parts=[]
    for kind in range(5):
     source_role=0 if kind==0 else role;a=blob(component,frame,source_role,kind);assert a==blob(component,ordinary,source_role,kind);parts.append(hashlib.sha256(a).hexdigest())
    rows.append(dict(owner=list(key),parts=parts));counts['owned_timing_blocks']+=1
   assert rows==baseline[index];counts['exact_qualified_source_frames']+=1
   reject_view(ftiming,frame,fi[4]);reject_view(stiming,scene,fi[4]);reject_view(ftiming,None,0);reject_view(stiming,None,0)
   if counts['budget_cases']<4:
    f=capture(C.byref(api),fi[5],ptr);assert f;frame_free(f);assert not capture(C.byref(api),fi[5]-1,ptr)
    s=prepare(frame,si[6]);assert s;scene_free(s);assert not prepare(frame,si[6]-1)
    f=take(C.byref(api),fi[5],C.cast(core.nfa_core_capture_background_take,P),C.cast(core.nfa_core_capture_owned_free,P),C.cast(core.nfa_core_capture_source_world_take,P),C.cast(core.nfa_core_capture_source_world_free,P),ptr);assert f
    for role in range(fi[4]):assert blob(ftiming,f,role)==blob(ftiming,frame,role)
    frame_free(f);counts['budget_cases']+=1
    if not g:g=gpu_open();assert g
    a=(C.c_ubyte*(3840*2160*4))();b=(C.c_ubyte*len(a))();assert gpu_draw(g,scene,3840,2160,3240,2160,a,len(a)) and gpu_draw(g,un_scene,3840,2160,3240,2160,b,len(b)) and bytes(a)==bytes(b);counts['endpoint_pixels_exact']+=3840*2160
   if not counts['forgeries']:
    assert not capture(C.byref(api),maximum,None)
    for offset,value in [(0,999),(8,999),(32,fi[1]+10),(48,fi[1]+10),(80,0),(88,0),(96,2),(104,2),(128,float('nan')),(136,12345.)]:
     def forge(core_handle,epoch,serial,begin,end,destination,capacity,offset=offset,value=value):
      raw=bytearray(metadata([epoch,serial,begin,end]));struct.pack_into('<d' if isinstance(value,float) else '<Q',raw,offset,value)
      if destination:
       if capacity<184:return 0
       C.memmove(destination,bytes(raw),184)
      return 184
     callback=READ(forge);assert not capture(C.byref(api),maximum,C.cast(callback,P));counts['forgeries']+=1
    errors=[]
    thread=threading.Thread(target=lambda:errors.append(capture(C.byref(api),maximum,ptr)));thread.start();thread.join();assert errors==[None];counts['wrong_thread_capture_rejected']+=1
   if previous:
    old_frame,old_scene,old_times=previous
    for ar,at in enumerate(old_times):
     for br,bt in enumerate(times):
      expected=bt[1]>at[1] and 0<bt[3]-at[3]<=8 and 0<bt[6]-at[6]<=8
      target=(at[6]+bt[6])/2;value=C.c_double(-7);accepted=alpha(old_scene,ar,scene,br,target,C.byref(value));assert bool(accepted)==expected
      if expected:
       assert abs(value.value-.5)<1e-12;counts['forward_capture_time_clocks']+=1
       for target_time,expected_alpha in [(at[6],0),(bt[6],1)]:assert alpha(old_scene,ar,scene,br,target_time,C.byref(value)) and value.value==expected_alpha;counts['exact_clock_endpoints']+=1
       for target_time in [at[6]-.25,bt[6]+.25,float('nan')]:value=C.c_double(-7);assert not alpha(old_scene,ar,scene,br,target_time,C.byref(value)) and value.value==-7;counts['clock_range_guards']+=1
       if detached is None:
        old_copy=prepare(old_frame,maximum);new_copy=prepare(frame,maximum);missing=normal_prepare(old_frame,maximum);assert old_copy and new_copy and missing;detached=(old_copy,new_copy,missing,ar,br,target,blob(stiming,old_copy,ar),blob(stiming,new_copy,br));retained_frame=capture(C.byref(api),maximum,ptr);assert retained_frame
      else:assert value.value==-7;counts['held_or_backward_clocks_rejected']+=1
    frame_free(old_frame);scene_free(old_scene)
   previous=(frame,scene,times);scene_free(un_scene);frame_free(ordinary)
finally:
 if previous:frame_free(previous[0]);scene_free(previous[1])
 if g:gpu_close(g)
 close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
assert detached and retained_frame
errors=[]
def detached_reader():
 try:
  a,b,missing,ar,br,target,old,new=detached;assert blob(stiming,a,ar)==old and blob(stiming,b,br)==new;value=C.c_double(-7);assert alpha(a,ar,b,br,target,C.byref(value)) and value.value==.5;value.value=-7;assert not alpha(missing,ar,b,br,target,C.byref(value)) and value.value==-7;assert len(blob(ftiming,retained_frame,0))==184
 except BaseException as e:errors.append(repr(e))
thread=threading.Thread(target=detached_reader);thread.start();thread.join();assert not errors,errors
frame_free(retained_frame)
for s in detached[:3]:scene_free(s)
for n in ['background','geometry']:
 values=(Q*3)();assert fn(core,'nfa_core_capture_owned_'+n+'_info',[P])(values) and values[0]==values[1]>0;counts['balanced_'+n+'_transfer_allocations']=values[0]
assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_OWNED_CAPTURE_TIME_FRAMES_SCENES_AND_CLOCKS',counts=dict(counts),scene_frame_and_core_destruction_survived=True,detached_reader_thread=True,original_frames_pcm_and_source_components_exact=True,pcm_frames=samples,pcm_sha256=digest.hexdigest(),core_sha256=sha(out/'timing-core.dll'),scene_dll_sha256=sha(out/'timed-scenes.dll'),test_sha256=sha(Path(__file__)),protected_sha256=protected,full_scene_60fps=False,live_enabled=False)
(out/'owned-timing-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
