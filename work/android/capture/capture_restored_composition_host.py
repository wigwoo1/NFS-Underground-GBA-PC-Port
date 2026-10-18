import ctypes as C,os,hashlib,json,struct,sys,subprocess
from pathlib import Path
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port'); out=Path(r'C:\NFSUG-Workspace\NFSUG-android-restored-composition-local')
if '--clean-child' not in sys.argv:
 env=os.environ.copy()
 for name in ('NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS'):env.pop(name,None)
 raise SystemExit(subprocess.call([sys.executable,__file__,'--clean-child'],env=env))
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
source_core_enable=api('capture_source_world_enable',[P,C.c_int])

skyen=api('capture_sky_enable',[P,C.c_int]);sky_scene=api('capture_sky_scene',[P,Q,U,P,S],S)
fixture_out=Path(r'C:\NFSUG-Workspace\NFSUG-restored-composition-fixtures');fixture_out.mkdir(exist_ok=True)
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

road_commands=d.nf_owned_road_commands;road_commands.argtypes=[Q,U,U,U,U,C.POINTER(U),U];road_commands.restype=U
road_asset=d.nf_owned_road_asset;road_asset.argtypes=[Q,U,U,U,U,U,P,S];road_asset.restype=S
road_identity=d.nf_owned_road_command_identity;road_identity.argtypes=road_commands.argtypes;road_identity.restype=U
road_diagnostic=d.nf_owned_road_asset_diagnostic;road_diagnostic.argtypes=[Q,U,U,U,U,U,C.POINTER(U)];road_diagnostic.restype=C.c_int
all_2d=d.nf_owned_all_2d_enable;all_2d.restype=C.c_int
operation_2d=d.nf_owned_2d_operation;operation_2d.argtypes=[Q,U,U,U,U,P,S,C.POINTER(Q)];operation_2d.restype=S
full_replay=d.nf_owned_full_replay_enable;full_replay.restype=C.c_int
full_read=d.nf_owned_full_replay_read;full_read.argtypes=[Q,U,U,P,S];full_read.restype=S
audit_enable=d.nf_owned_event_audit_enable;audit_enable.restype=C.c_int
audit_read=d.nf_owned_event_audit_read;audit_read.argtypes=[Q,U,U,P,S,C.POINTER(U)];audit_read.restype=S
journal_open=d.nf_owned_road_journal_open;journal_open.argtypes=[C.c_char_p];journal_open.restype=C.c_int
journal_close=d.nf_owned_road_journal_close;journal_close.restype=None
road_records=[]
def capture_roads(owners):
 for owner in owners:
  if any(r['owner']==owner for r in road_records):continue
  record=dict(owner=owner,commands=[],assets=[])
  for passno in range(4):
   commands=(U*(144*3))();count=road_commands(owner['epoch'],owner['serial'],owner['begin'],owner['end'],passno,commands,144)
   identities=(U*(144*5))();assert road_identity(owner['epoch'],owner['serial'],owner['begin'],owner['end'],passno,identities,144)==count
   for i in range(count):
    ordinal,kind,secondary=commands[i*3:i*3+3];item=dict(identity=list(identities[i*5:i*5+5]),passno=passno,ordinal=ordinal,kind=kind,secondary=secondary);record['commands'].append(item)
    if kind!=1:continue
    n=road_asset(owner['epoch'],owner['serial'],owner['begin'],owner['end'],passno,ordinal,None,0)
    if not n:
     item['asset_available']=False;detail=(U*16)();assert road_diagnostic(owner['epoch'],owner['serial'],owner['begin'],owner['end'],passno,ordinal,detail);item['diagnostic']=list(detail);continue
    buf=C.create_string_buffer(n);assert road_asset(owner['epoch'],owner['serial'],owner['begin'],owner['end'],passno,ordinal,buf,n)==n
    filename=f"road-{owner['serial']}-{passno}-{ordinal}.nfre";(fixture_out/filename).write_bytes(buf.raw);item['asset_available']=True;record['assets'].append(dict(filename=filename,sha256=hashlib.sha256(buf.raw).hexdigest(),bytes=n))
  operations=[]
  for ordinal in range(32):
   meta=(Q*8)();n=operation_2d(owner['epoch'],owner['serial'],owner['begin'],owner['end'],ordinal,None,0,meta);assert meta[1]==0
   if ordinal>=meta[0]:break
   assert n;buf=C.create_string_buffer(n);assert operation_2d(owner['epoch'],owner['serial'],owner['begin'],owner['end'],ordinal,buf,n,meta)==n
   name=f"operation-{owner['serial']}-{ordinal}.bin";(fixture_out/name).write_bytes(buf.raw);operations.append(dict(filename=name,meta=list(meta),sha256=hashlib.sha256(buf.raw).hexdigest()))
  record['operations_2d']=operations
  n=full_read(owner['epoch'],owner['end']+1,owner['page'],None,0);assert n==38400
  buf=C.create_string_buffer(n);assert full_read(owner['epoch'],owner['end']+1,owner['page'],buf,n)==n
  name=f"full-native-{owner['serial']}.bin";(fixture_out/name).write_bytes(buf.raw);record['full_replay']=dict(filename=name,sha256=hashlib.sha256(buf.raw).hexdigest(),refresh=owner['end']+1)
  audit_meta=(U*2)();n=audit_read(owner['epoch'],owner['end']+1,owner['page'],None,0,audit_meta);assert n==192000 and audit_meta[1]==0
  buf=C.create_string_buffer(n);assert audit_read(owner['epoch'],owner['end']+1,owner['page'],buf,n,audit_meta)==n
  name=f"provenance-{owner['serial']}.bin";(fixture_out/name).write_bytes(buf.raw);record['provenance']=dict(filename=name,sha256=hashlib.sha256(buf.raw).hexdigest(),events=audit_meta[0],failed=audit_meta[1])
  road_records.append(record)

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
saved={};failures=[];audio_hash=hashlib.sha256();audio_frames=0;pcm=(C.c_int16*8192)()
selection=json.loads(Path('C:/NFSUG-Workspace/NFSUG-source-display-binding-fixtures/manifest.json').read_text());targets={r['refresh'] for r in selection['fixtures']}
try:
 assert load(h,state,len(state)) and en(h,1) and layers(h,1) and source_core_enable(h,1) and bg_enable(rom[0x627700:0x647700],131072) and skyen(h,1) and all_2d() and full_replay() and audit_enable() and journal_open(os.fsencode(fixture_out/'original-road-events.nrj'))
 initial=(Q*4)();assert timing(h,initial)
 with open(r'C:\NFSUG-Workspace\NFSUG-android-capture-local\capture-off\frames.raw','rb') as oracle:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   while True:
    amount=audio(h,pcm,4096)
    if not amount:break
    assert amount<=4096;audio_hash.update(C.string_at(pcm,amount*4));audio_frames+=amount
   info=(Q*5)()
   if not infof(h,info) or info[1] not in targets:continue
   n=sky_scene(h,info[0],info[1],None,0)
   if not n:continue
   buf=C.create_string_buffer(n);assert sky_scene(h,info[0],info[1],buf,n)==n;kind=struct.unpack_from('<Q',buf.raw,40)[0]
   key=str(info[1])
   if key in saved:continue
   corrected,metadata=corrected_bundle(buf.raw)
   if corrected is None:failures.append(dict(refresh=info[1],reason='classified-packet',detail=metadata));continue
   joined,coverage=background_bundle(corrected,metadata)
   if joined is None:failures.append(dict(refresh=info[1],reason=coverage,owners=metadata));continue
   capture_roads(metadata)
   name=('whole' if kind==1 else 'split')+'-'+key;(fixture_out/f'race-background-{name}.nrb').write_bytes(joined);
   (fixture_out/f'sky-scene-{name}.nsb').write_bytes(corrected);saved[key]=dict(kind=kind,filename=f'race-background-{name}.nrb',refresh=info[1],owners=metadata,background_coverage=coverage,background_bundle_sha256=hashlib.sha256(joined).hexdigest(),snapshot_sha256=hashlib.sha256(corrected).hexdigest());print(name,flush=True)
finally:journal_close();bg_disable();source_disable();close(h)
assert audio_frames==443007 and audio_hash.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
collected={o['serial'] for r in saved.values() for o in r['owners']};restored={7,17,18,19,61,62,63,67,69}
report=dict(road_records=road_records,result='RESTORED_COMPOSITION_CAPTURE_AUDIT',original_frames=600,original_timing=True,audio_frames=audio_frames,audio_sha256=audio_hash.hexdigest(),fixtures=saved,failed_attempts=failures,selected_refreshes=sorted(targets),restored_owners_collected=sorted(restored&collected),all_restored_owners_collected=restored<=collected,diagnostic_only=True,live_sink_replaced=False)
(fixture_out/'source-fixture-capture-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('road_records','fixtures')},indent=2));print('saved_snapshots',len(saved),'road_owner_records',len(road_records))
