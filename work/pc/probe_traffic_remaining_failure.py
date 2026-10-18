"""Diverse steering coverage: exact original pixels/audio/clocks plus source pose movement.

This is an offscreen scripted exercise, not lap completion or live pacing proof.
"""
from pathlib import Path
import ctypes as C,hashlib,json,math,os,struct,time
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-remaining-failure-probe';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();current=base/'NFSUG-pc-traffic-remaining-failure-core';baseline=base/'NFSUG-pc-source-transfer-core';adapterdir=base/'NFSUG-pc-source-reader-direct-tests'
cr=json.loads((current/'traffic-remaining-failure-build-report.json').read_text());br=json.loads((baseline/'source-transfer-core-test-report.json').read_text());ar=json.loads((adapterdir/'reader-direct-test-report.json').read_text())
assert cr['result']=='BUILT_READONLY_TRAFFIC_REMAINING_FAILURE_CORE' and cr['core_sha256']==sha(current/'capture-host.dll') and br['core_sha256']==sha(baseline/'capture-host.dll') and ar['dll_sha256']==sha(adapterdir/'source-reader.dll')
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
pcm=(C.c_int16*8192)();failures=[];poses=[];complete=0;anchor=None;started=time.monotonic();ledger=[]
try:
 for i in range(3630):
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
 freeze=fn(new,'nfa_core_capture_traffic_remaining_failure',[P,P,S]);frozen=(U*640)(*([0x1234abcd]*640));h=items[1]['h']
 assert not freeze(h,frozen,639) and all(x==0x1234abcd for x in frozen)
 assert not freeze(None,frozen,640) and not freeze(h,None,640)
 before_inspection=(Q*4)();after_inspection=(Q*4)();assert items[1]['f']['timing'](h,before_inspection)
 assert freeze(h,frozen,640) and tuple(frozen[:3])==(0x3146544e,1,640)
 assert items[1]['f']['timing'](h,after_inspection) and tuple(before_inspection)==tuple(after_inspection)
 (out/'remaining-failure.bin').write_bytes(bytes(frozen));(out/'remaining-failure.json').write_text(json.dumps(list(frozen),indent=2))
 assert items[1]['f']['load_state'](h,state,len(state));sentinel=(U*640)(*([0x1234abcd]*640));assert not freeze(h,sentinel,640) and all(x==0x1234abcd for x in sentinel)
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
report=dict(frozen_failure=list(frozen),short_null_invalid_atomic=True,inspection_clock_neutral=True,state_reload_clears_diagnostic=True,post_reload_traffic_rotation_stats=list(traffic_stats),result='VERIFIED_REMAINING_FAILURE_FOCUSED_REPLAY',steps=3630,complete_source_frames=complete,failures=failures,poses=poses,first_model_identity=list(anchor) if anchor else None,pose_horizontal_path_world_units=path,pose_horizontal_span_world_units=span,last1200_steps_horizontal_span_world_units=tailspan,all3630_original_pixels_exact=True,audio_frames=items[0]['samples'],audio_sha256=items[0]['audio'].hexdigest(),original_clocks_exact=True,allocation_lifetimes_balanced=True,rom_state_sha256=before,input_keys=ledger,core_sha256=sha(current/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),reader_sha256=sha(adapterdir/'source-reader.dll'),script_sha256=sha(Path(__file__)),diagnostic_elapsed_seconds=time.monotonic()-started,lap_completion_verified=False,full_scene_60fps=False,scope='Offscreen diverse steering; original pixels/audio/clocks verified. Pose movement is not lap/track progress or live pacing proof.')
(out/'diverse-route-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['poses','input_keys','failures']},indent=2));print('late_failures',json.dumps(failures[10:30]))
