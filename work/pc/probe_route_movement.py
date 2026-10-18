"""Track an original object's position across model-descriptor changes.

Uses immutable completed original packets, not current framebuffer matching.
"""
from pathlib import Path
import ctypes as C,hashlib,json,math,os,struct
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-diverse-route-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();core=base/'NFSUG-pc-model-context-handoff';report=json.loads((core/'context-refresh-core-test-report.json').read_text());assert report['core_sha256']==sha(core/'capture-host.dll')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(core/'capture-host.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t;I=C.c_int
class Section(C.Structure):_fields_=[('data',P),('size',S)]
class Packet(C.Structure):_fields_=[('serial',U),('begin',U),('end',U),('page',U),('sections',Section*5)]
def fn(n,args,result=I):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);step=fn('nfa_core_step',[P,U]);timing=fn('nfa_core_timing',[P,P]);audio=fn('nfa_core_read_audio',[P,P,S],S);info=fn('nfa_core_capture_layer_info',[P,P]);bundle=fn('nfa_core_capture_bundle',[P,Q,U,P,S],S);background=fn('nfa_core_capture_background_scene',[P,Q,U,P,S],S);sky=fn('nfa_core_capture_sky_scene',[P,Q,U,P,S],S);rejection=fn('nfa_core_capture_scene_rejection_info',[P,P,S]);context=fn('nfa_core_capture_context_rejection_info',[P,P,S]);view=fn('nf_scene_packet_view',[P,S,P]);getmodel=fn('nf_scene_packet_model',[P,U,P]);count=fn('nf_scene_packet_model_count',[P],U)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';statepath=root/'work/integration-0.state';state=statepath.read_bytes();before={str(p):sha(p) for p in (rom,statepath)};h=op(os.fsencode(rom));assert h and load(h,state,len(state))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn('nfa_core_'+n,[P,I])(h,1)
initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();pcmhash=hashlib.sha256();samples=0;poses=[];all_poses=[];missing=[];capture_samples=[];camera_samples=[];anchor=None
try:
 for i in range(6000):
  phase=i%1200;keys=1|(32 if 180<=phase<500 else 16 if 500<=phase<720 else 0);assert step(h,keys)==1
  tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+i+1 and tick[3]==i+1
  while True:
   n=audio(h,pcm,4096)
   if not n:break
   samples+=n;pcmhash.update(C.string_at(pcm,n*4))
  if (i+1)%30:continue
  m=(Q*5)();assert info(h,m);n=bundle(h,m[0],m[1],None,0)
  background_bytes=background(h,m[0],m[1],None,0);sample=dict(step=i+1,display=list(m),bundle_bytes=n,background_bytes=background_bytes)
  if not background_bytes:
   detail=(U*192)();ctx=(U*20)();assert rejection(h,detail,192) and context(h,ctx,20)
   sample.update(sky_scene_bytes=sky(h,m[0],m[1],None,0),native_scene_stats=list(detail[6:10]),rejection_detail=list(detail[16:25]),model_rejection=list(detail[48:56]),context_rejection=list(ctx[:16]),handoff_stats=list(ctx[16:]))
  capture_samples.append(sample)
  if not n:missing.append(i+1);continue
  buf=C.create_string_buffer(n);assert bundle(h,m[0],m[1],buf,n)==n;head=struct.unpack_from('<16Q',buf.raw);owner=head[7]-1;offset,size=head[8+owner*2:10+owner*2];packet=Packet();assert view(C.cast(C.byref(buf,offset),P),size,C.byref(packet));worlds=struct.unpack('<I',C.string_at(packet.sections[1].data+4,4))[0]
  for j in range(count(C.byref(packet))):
   identity=struct.unpack('<5I',C.string_at(packet.sections[4].data+8+(worlds+j)*20,20));model=Section();assert getmodel(C.byref(packet),j,C.byref(model))
   pose=struct.unpack('<7d',C.string_at(model.data+104,56));assert all(math.isfinite(v) for v in pose)
   camera=struct.unpack('<7d',C.string_at(model.data+48,56))
   row=dict(step=i+1,epoch=int(m[0]),identity=list(identity),position=list(pose[:3]),rotation=list(pose[3:]),camera_position=list(camera[:3]));all_poses.append(row)
   if j==0:camera_samples.append(dict(step=i+1,position=list(camera[:3])))
   if anchor is None:anchor=(int(m[0]),*identity[:3])
   if (int(m[0]),*identity[:3])==anchor:poses.append(row)
  after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
  if (i+1)%1200==0:print(json.dumps(dict(step=i+1,tracked=len(poses),model_samples=len(all_poses))),flush=True)
finally:close(h)
assert before=={str(p):sha(p) for p in (rom,statepath)}
def span(rows):return [max(r['position'][a] for r in rows)-min(r['position'][a] for r in rows) for a in [0,2]] if rows else []
def dist(a,b):return math.hypot(a[0]-b[0],a[2]-b[2])
reference=json.loads((out/'diverse-route-report.json').read_text());assert reference['audio_sha256']==pcmhash.hexdigest() and reference['audio_frames']==samples
tracks={}
for row in all_poses:tracks.setdefault(tuple([row['epoch'],*row['identity'][:3]]),[]).append(row)
track_summaries=[dict(identity=list(k),samples=len(v),descriptor_ids=sorted({r['identity'][3] for r in v}),horizontal_span_world_units=span(v),last_step=v[-1]['step']) for k,v in tracks.items()]
result=dict(result='ORIGINAL_OBJECT_ROUTE_POSE_OBSERVATIONS',capture_samples=capture_samples,camera_samples=camera_samples,camera_span=span(camera_samples),source_object_tracks=track_summaries,anchor=list(anchor) if anchor else None,tracked_samples=len(poses),all_model_samples=len(all_poses),missing_bundle_samples=missing,poses=poses,all_model_poses=all_poses,descriptor_ids=sorted({r['identity'][3] for r in poses}),horizontal_span_world_units=span(poses),last1200_steps_span_world_units=span([r for r in poses if r['step']>=4800]),horizontal_path_world_units=sum(dist(a['position'],b['position']) for a,b in zip(poses,poses[1:])),audio_frames=samples,audio_sha256=pcmhash.hexdigest(),core_sha256=sha(core/'capture-host.dll'),script_sha256=sha(Path(__file__)),rom_state_sha256=before,game_clocks_exact=True,diagnostic_reads_do_not_step=True,lap_completion_verified=False,full_scene_60fps=False,scope='Immutable original model poses; same source object/epoch tracked across descriptor variants. Movement alone does not prove lap progress.')
(out/'route-movement-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['poses','all_model_poses','capture_samples','camera_samples','source_object_tracks']},indent=2))
