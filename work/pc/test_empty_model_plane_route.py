"""Diverse steering coverage: exact original pixels/audio/clocks plus source pose movement.

This is an offscreen scripted exercise, not lap completion or live pacing proof.
"""
from pathlib import Path
import ctypes as C,hashlib,json,math,os,struct,time
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-empty-model-plane-route-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();current=base/'NFSUG-pc-traffic-rotation-draw-camera-core';baseline=base/'NFSUG-pc-source-transfer-core';adapterdir=base/'NFSUG-pc-source-reader-direct-tests'
cr=json.loads((current/'traffic-draw-camera-build-report.json').read_text());br=json.loads((baseline/'source-transfer-core-test-report.json').read_text());ar=json.loads((adapterdir/'reader-direct-test-report.json').read_text())
assert cr['result']=='BUILT_GUARDED_TRAFFIC_DRAW_CAMERA_CORE' and cr['core_sha256']==sha(current/'capture-host.dll') and br['core_sha256']==sha(baseline/'capture-host.dll') and ar['dll_sha256']==sha(adapterdir/'source-reader.dll')
for report in [cr,ar]:
 for n,h in report.get('maintained_source_sha256',report.get('source_sha256',{})).items():assert sha(here/n)==h,n
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):new=C.CDLL(str(current/'capture-host.dll'));old=C.CDLL(str(baseline/'capture-host.dll'));reader=C.CDLL(str(adapterdir/'source-reader.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
class Section(C.Structure):_fields_=[('data',P),('size',S)]
class Packet(C.Structure):_fields_=[('serial',U),('begin',U),('end',U),('page',U),('sections',Section*5)]
def fn(d,name,args,result=I):f=getattr(d,name);f.argtypes=args;f.restype=result;return f
bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P);cap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);free=fn(reader,'nf_pc_source_frame_free',[P],None);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);meta=fn(reader,'nf_pc_source_frame_info',[P,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)]);failure=fn(reader,'nf_pc_source_reader_last_failure',[P,P])
view=fn(new,'nf_scene_packet_view',[P,S,P]);getmodel=fn(new,'nf_scene_packet_model',[P,U,P]);modelcount=fn(new,'nf_scene_packet_model_count',[P],U)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';statepath=root/'work/integration-0.state';state=statepath.read_bytes();before={str(p):sha(p) for p in (rom,statepath)}
items=[]
for d in [old,new]:
 fs={n:fn(d,'nfa_core_'+n,a,z) for n,a,z in [('open',[C.c_char_p],P),('close',[P],None),('load_state',[P,P,S],I),('step',[P,U],I),('pixels',[P],P),('read_audio',[P,P,S],S),('timing',[P,P],I)]}
 h=fs['open'](os.fsencode(rom));assert h and fs['load_state'](h,state,len(state));t=(Q*4)();assert fs['timing'](h,t);items.append(dict(d=d,h=h,f=fs,initial=list(t),audio=hashlib.sha256(),samples=0))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(new,'nfa_core_'+n,[P,I])(items[1]['h'],1)
assert fn(new,'nfa_core_geometry_cache_enable',[P,I])(items[1]['h'],1)
api=API(C.sizeof(API),items[1]['h'],*[C.cast(getattr(new,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api))
r=rop(C.byref(api),64*1024*1024,C.cast(new.nfa_core_capture_background_take,P),C.cast(new.nfa_core_capture_owned_free,P),C.cast(new.nfa_core_capture_source_world_take,P),C.cast(new.nfa_core_capture_source_world_free,P));assert r
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 scene_base=C.CDLL(str(base/'NFSUG-pc-empty-model-plane-tests/before/source-scene.dll'));scene_new=C.CDLL(str(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll'))
scene_build=json.loads((base/'NFSUG-pc-empty-model-plane-tests/empty-plane-build-report.json').read_text());assert scene_build['dll_sha256']==sha(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll') and scene_build['baseline_dll_sha256']==sha(base/'NFSUG-pc-empty-model-plane-tests/before/source-scene.dll')
prep=[fn(d,'nf_pc_scene_prepare',[P,S],P) for d in [scene_base,scene_new]];si=[fn(d,'nf_pc_scene_info',[P,P]) for d in [scene_base,scene_new]];sf=[fn(d,'nf_pc_scene_free',[P],None) for d in [scene_base,scene_new]];ci=[fn(d,'nf_pc_scene_command_info',[P,U,P]) for d in [scene_base,scene_new]];cb=[fn(d,'nf_pc_scene_command_buffer',[P,U,U,P,P]) for d in [scene_base,scene_new]];recovered=[];baseline_prepared=candidate_prepared=0;commands_exact=0;buffer_bytes_exact=0
pcm=(C.c_int16*8192)();failures=[];poses=[];complete=0;anchor=None;started=time.monotonic();ledger=[]
try:
 for i in range(6000):
  # Same established periodic steering schedule as capture_occlusion_route.py.
  phase=i%1200;keys=1|(32 if 180<=phase<500 else 16 if 500<=phase<720 else 0);ledger.append(keys)
  for item in items:
   h=item['h'];f=item['f'];assert f['step'](h,keys)==1;t=(Q*4)();assert f['timing'](h,t) and tuple(t[:2])==(16777216,280896) and t[2]==item['initial'][2]+i+1 and t[3]==i+1
   while True:
    n=f['read_audio'](h,pcm,4096)
    if not n:break
    item['samples']+=n;item['audio'].update(C.string_at(pcm,n*4))
  assert C.string_at(items[0]['f']['pixels'](items[0]['h']),153600)==C.string_at(items[1]['f']['pixels'](items[1]['h']),153600),('Original framebuffer differs',i+1)
  frame=cap(r,64*1024*1024)
  if not frame:
   record=(Q*6)();assert failure(r,record);failures.append(dict(step=i+1,detail=list(record)))
  else:
   try:
    complete+=1;m=(Q*8)();assert meta(frame,m)
    prepared=[f(frame,64*1024*1024) for f in prep]
    assert prepared[1],('Candidate still rejects captured source frame',i+1)
    try:
     candidate_prepared+=1;new_info=(Q*8)();assert si[1](prepared[1],new_info)
     if not prepared[0]:recovered.append(dict(step=i+1,frame_info=list(m),prepared_info=list(new_info)))
     else:
      baseline_prepared+=1;old_info=(Q*8)();assert si[0](prepared[0],old_info) and tuple(old_info)==tuple(new_info)
      for command in range(old_info[3]):
       old_meta=(Q*16)();new_meta=(Q*16)();assert ci[0](prepared[0],command,old_meta) and ci[1](prepared[1],command,new_meta) and tuple(old_meta)==tuple(new_meta);commands_exact+=1
       for kind in range(2):
        old_ptr=P();new_ptr=P();old_size=S();new_size=S();assert cb[0](prepared[0],command,kind,C.byref(old_ptr),C.byref(old_size)) and cb[1](prepared[1],command,kind,C.byref(new_ptr),C.byref(new_size)) and old_size.value==new_size.value
        assert C.string_at(old_ptr,old_size.value)==C.string_at(new_ptr,new_size.value),('Working command changed',i+1,command,kind);buffer_bytes_exact+=old_size.value
    finally:
     for index,packet in enumerate(prepared):sf[index](packet)
    if (i+1)%30==0:
     ptr=P();size=S();assert component(frame,int(m[4])-1,1,C.byref(ptr),C.byref(size));packet=Packet();assert view(ptr,size.value,C.byref(packet));worlds=struct.unpack('<I',C.string_at(packet.sections[1].data+4,4))[0]
     for j in range(modelcount(C.byref(packet))):
      identity=struct.unpack('<5I',C.string_at(packet.sections[4].data+8+(worlds+j)*20,20))
      if anchor is None:anchor=identity
      if identity!=anchor:continue
      model=Section();assert getmodel(C.byref(packet),j,C.byref(model)) and model.size>=160
      pose=struct.unpack('<7d',C.string_at(model.data+104,56));assert all(math.isfinite(v) for v in pose)
      poses.append(dict(step=i+1,identity=list(identity),position=list(pose[:3]),rotation=list(pose[3:])));break
   finally:free(frame)
  if (i+1)%600==0:print(json.dumps(dict(step=i+1,complete=complete,failures=len(failures),poses=len(poses))),flush=True)
 for item in items:assert item['samples']==items[0]['samples'] and item['audio'].hexdigest()==items[0]['audio'].hexdigest()
finally:
 traffic_stats=(Q*6)();assert fn(new,'nfa_core_capture_traffic_rotation_stats',[P,P])(items[1]['h'],traffic_stats)
 rclose(r)
 for item in items:item['f']['close'](item['h'])
for kind in ['background','geometry']:
 stats=(Q*3)();assert fn(new,'nfa_core_capture_owned_'+kind+'_info',[P])(stats) and stats[0]==stats[1]
assert before=={str(p):sha(p) for p in (rom,statepath)}
def dist(a,b):return math.hypot(a[0]-b[0],a[2]-b[2])
path=sum(dist(a['position'],b['position']) for a,b in zip(poses,poses[1:]));span=[max(p['position'][axis] for p in poses)-min(p['position'][axis] for p in poses) for axis in [0,2]] if poses else []
trailing=[p for p in poses if p['step']>=4800];tailspan=[max(p['position'][axis] for p in trailing)-min(p['position'][axis] for p in trailing) for axis in [0,2]] if trailing else []
assert baseline_prepared==5807 and candidate_prepared==5970 and len(recovered)==163
report=dict(recovered=recovered,baseline_prepared=baseline_prepared,candidate_prepared=candidate_prepared,working_commands_exact=commands_exact,working_vertex_plane_bytes_exact=buffer_bytes_exact,scene_build_receipt_sha256=sha(base/'NFSUG-pc-empty-model-plane-tests/empty-plane-build-report.json'),traffic_rotation_stats=list(traffic_stats),result='VERIFIED_EMPTY_MODEL_PLANE_FULL_ROUTE_RECOVERY',steps=6000,complete_source_frames=complete,failures=failures,poses=poses,first_model_identity=list(anchor) if anchor else None,pose_horizontal_path_world_units=path,pose_horizontal_span_world_units=span,last1200_steps_horizontal_span_world_units=tailspan,all6000_original_pixels_exact=True,audio_frames=items[0]['samples'],audio_sha256=items[0]['audio'].hexdigest(),original_clocks_exact=True,allocation_lifetimes_balanced=True,rom_state_sha256=before,input_keys=ledger,core_sha256=sha(current/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),reader_sha256=sha(adapterdir/'source-reader.dll'),script_sha256=sha(Path(__file__)),diagnostic_elapsed_seconds=time.monotonic()-started,lap_completion_verified=False,full_scene_60fps=False,scope='Offscreen diverse steering; original pixels/audio/clocks verified. Pose movement is not lap/track progress or live pacing proof.')
(out/'diverse-route-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['poses','input_keys','failures','recovered']},indent=2));print('late_failures',json.dumps(failures[10:30]))
