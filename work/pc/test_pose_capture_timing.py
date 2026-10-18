from pathlib import Path
import ctypes as C,os,json,hashlib,struct,collections
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-pose-capture-timing-tests'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'timing-build-report.json').read_text());assert sha(out/'capture-host.dll')==build['core_sha256']
reader_path=base/'NFSUG-pc-owner-pose-draw-tests/owner-pose-draw.dll'
with os.add_dll_directory('C:/msys64/mingw64/bin'):reader=C.CDLL(str(reader_path))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);capture=fn(reader,'nf_pc_source_frame_capture',[P,S],P);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]}
def part(raw,i):at,n=struct.unpack_from('<2Q',raw,64+i*16);assert at<=len(raw) and n<=len(raw)-at;return raw[at:at+n]
def blob(f,*a):p=P();n=S();assert f(*a,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def route(path,diagnostic):
 for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
 with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(path))
 op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);h=op(os.fsencode(rom));data=state.read_bytes();assert h and load(h,data,len(data))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api))
 getter=fn(core,'nf_pc_source_pose_timing',[Q,U,U,U,P,S,P,S]) if diagnostic else None
 baseline=(Q*4)();assert timing(h,baseline);pcm=(C.c_int16*8192)();digest=hashlib.sha256();frames=hashlib.sha256();samples=0;source_rows=[];observed=[];counts=collections.Counter();seen=set();saved=None
 try:
  with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
   for index in range(600):
    assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1
    image=C.string_at(pixels(h),153600);assert image==oracle.read(153600);frames.update(image);t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==baseline[2]+index+1 and t[3]==index+1
    while True:
     n=audio(h,pcm,4096)
     if not n:break
     samples+=n;digest.update(C.string_at(pcm,n*4))
    frame=capture(C.byref(api),64*1024*1024)
    if not frame:source_rows.append(None);continue
    try:
     fi=(Q*8)();assert frame_info(frame,fi);row=[];background=blob(component,frame,0,0);sky_root=part(background,0)
     for role in range(fi[4]):
      key=(Q*5)();assert owner(frame,role,key);pieces=[background]+[blob(component,frame,role,kind) for kind in range(1,5)];row.append(dict(owner=list(key),parts=[hashlib.sha256(v).hexdigest() for v in pieces]));counts['source_owners']+=1
      if not diagnostic:continue
      words=(Q*16)(*[0xcccccccccccccccc]*16);camera=C.create_string_buffer(56)
      assert getter(key[0],key[1],key[2],key[3],words,128,camera,56),list(key)
      assert list(words[:4])==list(key[:4]) and words[12]==key[4]
      assert key[2]<=words[4]<=words[5]<=key[3] and key[2]<=words[7]<=words[6]<=key[3] and key[2]<=words[8]<=words[9]<=key[3] and words[10]>0 and words[11]>0 and words[14]<=words[15]
      raw=pieces[1];models_at,models_n=struct.unpack_from('<2I',raw,36);model_section=raw[models_at:models_at+models_n]
      if model_section[:4]==b'NFM2':packets=[model_section]
      else:
       assert model_section[:4]==b'NML1';model_count=struct.unpack_from('<I',model_section,4)[0];packets=[]
       for j in range(model_count):a,n=struct.unpack_from('<2I',model_section,8+j*8);packets.append(model_section[a:a+n])
      for packet in packets:assert packet[:4]==b'NFM2' and packet[48:104]==camera.raw;counts['exact_nfm2_camera_bindings']+=1
      sky=part(sky_root,role+1);sky_refresh,sky_angle=struct.unpack_from('<2I',sky,16);assert key[2]<=sky_refresh<=key[3]
      for args in [(key[0]+1,key[1],key[2],key[3],words,128,camera,56),(key[0],key[1],key[2],key[3]+1,words,128,camera,56),(key[0],key[1],key[2],key[3],words,127,camera,56),(key[0],key[1],key[2],key[3],words,128,camera,55)]:
       w=bytes(words);c=camera.raw;assert not getter(*args) and bytes(words)==w and camera.raw==c;counts['atomic_rejection_guards']+=1
      token=tuple(key)
      if token not in seen:
       seen.add(token);observed.append(dict(owner=list(key),timing=list(words),sky_refresh=sky_refresh,sky_angle=sky_angle,nfm2_models=len(packets),camera_sha256=hashlib.sha256(camera.raw).hexdigest()))
      saved=(list(key),list(words),camera.raw)
     source_rows.append(row)
    finally:frame_free(frame)
  if diagnostic:
   assert saved;key,old_words,old_camera=saved;assert load(h,data,len(data));w=(Q*16)(*[0xcccccccccccccccc]*16);c=C.create_string_buffer(b'\xa5'*56,56);assert not getter(*key[:4],w,128,c,56) and list(w)==[0xcccccccccccccccc]*16 and c.raw==b'\xa5'*56;counts['epoch_reset_guard']+=1
 finally:close(h)
 assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 return dict(core_sha256=sha(path),original_frames_sha256=frames.hexdigest(),pcm_sha256=digest.hexdigest(),pcm_frames=samples,source_rows=source_rows,observations=observed,counts=dict(counts))
baseline_path=base/'NFSUG-pc-owner-pose-draw-tests/capture-host.dll';a=route(baseline_path,False);(out/'baseline-route.json').write_text(json.dumps(a,indent=2));print('baseline route PASS',flush=True)
b=route(out/'capture-host.dll',True);(out/'diagnostic-route.json').write_text(json.dumps(b,indent=2));assert a['source_rows']==b['source_rows'] and a['original_frames_sha256']==b['original_frames_sha256'] and a['pcm_sha256']==b['pcm_sha256']
observed=b['observations'];assert len(observed)>100
summary={}
for name,calc in {'owner_end_minus_render':lambda r:r['owner'][3]-r['timing'][6],'render_minus_sky':lambda r:r['timing'][6]-r['sky_refresh'],'builder_minus_sky':lambda r:r['timing'][5]-r['sky_refresh'],'query_minus_sky':lambda r:r['timing'][4]-r['sky_refresh'],'model_input_span':lambda r:r['timing'][9]-r['timing'][8]}.items():summary[name]=dict(sorted(collections.Counter(calc(r) for r in observed).items()))
assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_READONLY_POSE_CAPTURE_TIMING_PARITY',unique_owners=len(observed),counts=b['counts'],timing_distributions=summary,all_source_components_exact=True,original_frames_and_pcm_exact=True,baseline_core_sha256=a['core_sha256'],diagnostic_core_sha256=b['core_sha256'],reader_sha256=sha(reader_path),test_sha256=sha(Path(__file__)),build_report_sha256=sha(out/'timing-build-report.json'),protected_sha256=protected,full_scene_60fps=False,shipping_changed=False)
(out/'timing-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
