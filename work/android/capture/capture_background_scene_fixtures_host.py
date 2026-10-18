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

skyen=api('capture_sky_enable',[P,C.c_int]);sky_scene=api('capture_sky_scene',[P,Q,U,P,S],S)
fixture_out=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local');fixture_out.mkdir(exist_ok=True)
def corrected_bundle(original):
 h=list(struct.unpack_from('<16Q',original));nab=original[h[8]:h[8]+h[9]];nh=list(struct.unpack_from('<16Q',nab));sections=[];identities=[]
 for i in range(nh[7]):
  legacy=nab[nh[8+i*2]:nh[8+i*2]+nh[9+i*2]];serial,begin,end,page=struct.unpack_from('<4I',legacy,16);stage=U();n=source_packet(nh[3],serial,begin,end,None,0,C.byref(stage))
  if not n:return None,dict(serial=serial,stage=stage.value)
  buf=C.create_string_buffer(n);assert source_packet(nh[3],serial,begin,end,buf,n,C.byref(stage))==n
  assert struct.unpack_from('<4I',buf.raw,16)==(serial,begin,end,page);sections.append(buf.raw);identities.append(dict(epoch=nh[3],serial=serial,begin=begin,end=end,page=page,sha256=hashlib.sha256(buf.raw).hexdigest()))
 if nh[7]==1:sections.append(b'')
 sections.extend(nab[nh[8+i*2]:nh[8+i*2]+nh[9+i*2]] for i in (2,3));offset=128
 for i,part in enumerate(sections):nh[8+i*2]=offset;nh[9+i*2]=len(part);offset+=len(part)
 nh[2]=offset;newnab=struct.pack('<16Q',*nh)+b''.join(sections)
 tail=[original[h[10+i*2]:h[10+i*2]+h[11+i*2]] for i in range(h[7])]
 header=[0x3142534e,1,128+len(newnab)+sum(map(len,tail)),h[3],h[4],h[5],h[6],h[7],128,len(newnab),128+len(newnab),30568,0,0,0,0]
 if h[7]==2:header[12]=header[10]+30568;header[13]=30568
 return struct.pack('<16Q',*header)+newnab+b''.join(tail),identities

bg_enable=d.nf_owned_background_enable;bg_enable.argtypes=[P,U];bg_enable.restype=C.c_int
bg_disable=d.nf_owned_background_disable;bg_disable.restype=None
bg_read=d.nf_owned_background_read;bg_read.argtypes=[Q,U,U,P,S];bg_read.restype=S
def background_bundle(sky,owners):
 h=list(struct.unpack_from('<16Q',sky));parts=[sky];covered=[]
 for i,owner in enumerate(owners):
  n=bg_read(owner['epoch'],owner['end']+1,owner['page'],None,0)
  if n!=76800:return None,'missing-background'
  data=C.create_string_buffer(n);assert bg_read(owner['epoch'],owner['end']+1,owner['page'],data,n)==n;raw=data.raw;mask=raw[38400:];assert set(mask)<={0,1}
  if not any(mask):return None,'unowned-warmup'
  skystart=h[10+i*2];assert raw[10560:25696]==sky[skystart+56:skystart+15192] and all(mask[10560:25696])
  meta=(0x3147424e,1,76880,owner['epoch'],owner['serial'],owner['begin'],owner['end'],owner['end']+1,owner['page'],38400)
  parts.append(struct.pack('<10Q',*meta)+raw);covered.append(sum(mask))
 header=[0x3142524e,1,128+sum(map(len,parts)),h[3],h[4],h[5],h[6],h[7],0,0,0,0,0,0,0,0];offset=128
 for i,part in enumerate(parts):header[8+i*2]=offset;header[9+i*2]=len(part);offset+=len(part)
 return struct.pack('<16Q',*header)+b''.join(parts),covered

rompath=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';rom=rompath.read_bytes();state=(root/'work/integration-0.state').read_bytes();h=op(os.fsencode(rompath));assert h
saved={};failures=[]
try:
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and source_enable(rom,len(rom)) and bg_enable(rom[0x627700:0x647700],131072) and skyen(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as oracle:
  for i in range(64):
   assert step(h,1|(16 if 60<=i<120 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   info=(Q*5)()
   if not infof(h,info):continue
   n=sky_scene(h,info[0],info[1],None,0)
   if not n:continue
   buf=C.create_string_buffer(n);assert sky_scene(h,info[0],info[1],buf,n)==n;kind=struct.unpack_from('<Q',buf.raw,40)[0]
   if kind in saved:continue
   corrected,metadata=corrected_bundle(buf.raw)
   if corrected is None:failures.append(metadata);continue
   joined,coverage=background_bundle(corrected,metadata)
   if joined is None:failures.append(dict(reason=coverage,owners=metadata));continue
   name='whole' if kind==1 else 'split';(fixture_out/f'race-background-{name}.nrb').write_bytes(joined);
   (fixture_out/f'sky-scene-{name}.nsb').write_bytes(corrected);saved[kind]=dict(refresh=info[1],owners=metadata,background_coverage=coverage,background_bundle_sha256=hashlib.sha256(joined).hexdigest(),snapshot_sha256=hashlib.sha256(corrected).hexdigest());print(name,saved[kind],flush=True)
finally:bg_disable();source_disable();close(h)
assert set(saved)=={1,2};report=dict(result='PASS_SAME_RUN_BACKGROUND_SCENE_FIXTURES',original_frames=64,original_timing=True,fixtures=saved,failed_attempts=failures,diagnostic_only=True,live_sink_replaced=False);(fixture_out/'source-fixture-capture-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
