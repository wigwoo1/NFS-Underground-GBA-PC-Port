import ctypes as C,os,hashlib,json,struct,sys,subprocess
from pathlib import Path
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port'); out=Path(r'C:\NFSUG-Workspace\NFSUG-android-assembly-diagnostic-local')
if os.environ.get('NF_TEST_RACING_OWNED_CAPTURE')!='1' or os.environ.get('NF_LIVE_ROAD_ATTRIBUTES')!='1' or os.environ.get('NF_CAPTURE_MODEL_VIEWS')!='1':
 env=os.environ.copy();env['NF_TEST_RACING_OWNED_CAPTURE']='1';env['NF_LIVE_ROAD_ATTRIBUTES']='1';env['NF_CAPTURE_MODEL_VIEWS']='1'
 raise SystemExit(subprocess.call([sys.executable,__file__],env=env))
with os.add_dll_directory(r'C:\msys64\mingw64\bin'): d=C.CDLL(str(out/'capture-owned-text-host.dll'))
def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
P=C.c_void_p; Q=C.c_uint64; U=C.c_uint; S=C.c_size_t
op=api('open',[C.c_char_p],P); close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P)
en=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);texten=api('capture_text_enable',[P,C.c_int]);infof=api('capture_layer_info',[P,C.POINTER(Q)]);txt=api('capture_text',[P,Q,U,P,S],S);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S)
diag=d.nf_owned_text_diagnostic;diag.argtypes=[Q,U,C.POINTER(Q)];diag.restype=C.c_int
glyphcount=d.nf_owned_text_glyph_count;glyphcount.restype=U
trace=d.nf_owned_text_trace;trace.argtypes=[C.c_char_p];trace.restype=C.c_int

source_enable=d.nf_owned_source_world_enable;source_enable.argtypes=[P,S];source_enable.restype=C.c_int
source_state=d.nf_owned_source_world_state;source_state.argtypes=[Q,U,U,U,C.POINTER(Q)];source_state.restype=C.c_int
source_disable=d.nf_owned_source_world_disable;source_disable.restype=None
source_packet=d.nf_owned_source_world_packet;source_packet.argtypes=[Q,U,U,U,P,S,C.POINTER(U)];source_packet.restype=S
packet=api('capture_copy',[P,P,S],S)
assembly_detail=d.nf_owned_assembly_detail;assembly_detail.argtypes=[C.POINTER(U)];assembly_detail.restype=None
snapshot_detail=d.nf_visibility_snapshot_packet_detail;snapshot_detail.argtypes=[C.POINTER(U)];snapshot_detail.restype=None
command_detail=d.nf_scene_command_plan_detail;command_detail.argtypes=[C.POINTER(U)];command_detail.restype=None
object_detail=d.nf_owned_object_dispatch_detail;object_detail.argtypes=[Q,U,U,U,U,C.POINTER(U)];object_detail.restype=C.c_int
rompath=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';rom=rompath.read_bytes();h=op(os.fsencode(rompath));assert h
state=(root/'work/integration-0.state').read_bytes();seen=set();produced=[];failures={};diagnostics=[]
try:
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and source_enable(rom,len(rom))
 initial=(Q*4)();assert timing(h,initial)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as oracle:
  for i in range(64):
   assert step(h,1|(16 if 60<=i<120 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   n=packet(h,None,0)
   if not n:continue
   buf=C.create_string_buffer(n);assert packet(h,buf,n)==n;serial,begin,end=struct.unpack_from('<3I',buf.raw,16);info=(Q*5)();assert infof(h,info);key=(info[0],serial,begin,end)
   if key in seen:continue
   seen.add(key);details=(Q*24)();assert source_state(*key,details);diagnostics.append(dict(identity=list(key),model_inputs_valid=details[0],model_count=details[1],source_audit=details[2],render_snapshot=details[3],prepared_view=details[4],visibility_pose=details[5],visibility_stats=list(details[6:10]),capture_stage=details[10],palette_banks=details[11],pending_models=details[12],pending_failed=details[13],completed_model_valid=details[14],model_view_flag_seen=details[15],publish_detail=list(details[16:22]),publish_detail_valid=details[22],history_present=details[23]));stage=U();size=source_packet(*key,None,0,C.byref(stage))
   if not size:
    failures[str(stage.value)]=failures.get(str(stage.value),0)+1;assembly=(U*12)();snapshot=(U*6)();command=(U*18)();assembly_detail(assembly);snapshot_detail(snapshot);command_detail(command);diagnostics[-1]['assembly_detail']=list(assembly);diagnostics[-1]['snapshot_detail']=list(snapshot);diagnostics[-1]['command_detail']=list(command);io,isz=struct.unpack_from('<II',buf.raw,84);ids=buf.raw[io:io+isz];entries=struct.unpack_from('<I',ids,4)[0];diagnostics[-1]['original_model_identities']=[list(struct.unpack_from('<5I',ids,8+j*20)) for j in range(entries) if struct.unpack_from('<I',ids,8+j*20)[0]==3];dispatch=[]
    for source in [assembly[3]]+[identity[2] for identity in diagnostics[-1]['original_model_identities']]:
     detail=(U*64)();assert object_detail(*key,source,detail);dispatch.append(dict(source=source,summary=list(detail[:16]),visits=list(detail[16:32]),object_words=list(detail[32:])))
    diagnostics[-1]['object_dispatch']=dispatch;continue
   corrected=C.create_string_buffer(size);assert source_packet(*key,corrected,size,C.byref(stage))==size
   raw=corrected.raw;worldoff,worldbytes=struct.unpack_from('<II',raw,48);world=raw[worldoff:worldoff+worldbytes];count=struct.unpack_from('<I',world,4)[0];at=8
   for j in range(count):corners,w,ht=struct.unpack_from('<3I',world,at);at+=12+corners*40+w*ht*4
   modes=[0]*count
   if at<len(world):
    magic,nworld=struct.unpack_from('<II',world,at);assert magic==0x3149574e and nworld==count;at+=8
    for j in range(count):mode,bytes_=struct.unpack_from('<II',world,at);modes[j]=mode;at+=8+bytes_
   assert at==len(world)
   (out/f'source-world-{serial}.nsp').write_bytes(raw);produced.append(dict(serial=serial,bytes=size,modes=modes));print(produced[-1],flush=True)
finally:source_disable();close(h)
report=dict(prerequisite_diagnostics=diagnostics,result='SOURCE_WORLD_PATH_DIAGNOSTIC',original_frames=64,original_timing=True,source_scene_requests=len(seen),source_packets=produced,failure_stages=failures,live_sink_replaced=False)
(out/'source-world-path-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert produced,'No source-owned classified packets produced'

