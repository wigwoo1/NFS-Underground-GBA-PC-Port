import ctypes as C,os,hashlib,json,struct,sys,subprocess
from pathlib import Path
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port'); out=Path(r'C:\NFSUG-Workspace\NFSUG-android-owned-text-local')
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

bg_enable=d.nf_owned_background_enable;bg_enable.argtypes=[P,U];bg_enable.restype=C.c_int
bg_disable=d.nf_owned_background_disable;bg_disable.restype=None
bg_read=d.nf_owned_background_read;bg_read.argtypes=[Q,U,U,P,S];bg_read.restype=S
rompath=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';rom=rompath.read_bytes();table=rom[0x627700:0x647700];assert len(table)==131072
h=op(os.fsencode(rompath));assert h;state=(root/'work/integration-0.state').read_bytes();seen=set();records=[];missing=[]
try:
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and bg_enable(table,len(table))
 initial=(Q*4)();assert timing(h,initial)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as oracle:
  for i in range(64):
   assert step(h,1|(16 if 60<=i<120 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   n=packet(h,None,0)
   if not n:continue
   scene=C.create_string_buffer(n);assert packet(h,scene,n)==n;serial,begin,end,page=struct.unpack_from('<4I',scene.raw,16);info=(Q*5)();assert infof(h,info);key=(info[0],serial,begin,end,page)
   if key in seen:continue
   seen.add(key);size=bg_read(info[0],end+1,page,None,0)
   if not size:missing.append(key);continue
   assert size==76800;buf=C.create_string_buffer(bytes([165])*size,size)
   assert not bg_read(info[0],end+1,page,buf,size-1) and buf.raw==bytes([165])*size
   assert not bg_read(info[0]+1,end+1,page,buf,size) and buf.raw==bytes([165])*size
   assert bg_read(info[0],end+1,page,buf,size)==size;coverage=buf.raw[38400:];assert set(coverage)<={0,1}
   intervals=[];start=None
   for pos,value in enumerate(coverage+bytes([0])):
    if value and start is None:start=pos
    if not value and start is not None:intervals.append([start,pos]);start=None
   record=dict(epoch=info[0],serial=serial,begin=begin,end=end,page=page,refresh=end+1,covered_cells=sum(coverage),intervals=intervals,sha256=hashlib.sha256(buf.raw).hexdigest());records.append(record);(out/f'background-scene-{serial}.bin').write_bytes(buf.raw);print(record,flush=True)
 assert records and any(r['covered_cells']>0 for r in records)
 assert load(h,state,len(state)) and not bg_read(records[-1]['epoch'],records[-1]['refresh'],records[-1]['page'],None,0)
finally:bg_disable();close(h)
report=dict(result='PASS_INITIAL_BACKGROUND_SOURCE_CAPTURE_DIAGNOSTIC',original_frames=64,original_timing=True,source_records=records,missing=missing,complete_background_claim=False,android_runtime=False)
(out/'initial-background-source-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(records=len(records),missing=len(missing),coverage_counts=sorted({r['covered_cells'] for r in records}))))
