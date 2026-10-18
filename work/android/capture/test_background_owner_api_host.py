"""Normal core API wall-owner snapshots with unchanged original game timing and audio."""
from pathlib import Path
import ctypes as C,os,sys,subprocess,json,struct,hashlib,ast
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');native=base/'NFSUG-android-background-owner-native-local';out=base/'NFSUG-background-owner-api-fixtures';out.mkdir(exist_ok=True);fixtures=base/'NFSUG-wall-assets-fixtures'
if '--clean-child' not in sys.argv:
 env=os.environ.copy()
 for name in ('NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS'):env.pop(name,None)
 raise SystemExit(subprocess.call([sys.executable,__file__,'--clean-child'],env=env))
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(native/'capture-host.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint;S=C.c_size_t
def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
op=api('open',[C.c_char_p],P);close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S)
enable=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);source=api('capture_source_world_enable',[P,C.c_int]);wall=api('capture_wall_history_enable',[P,C.c_int]);read=api('capture_wall_history',[P,Q,U,U,U,P,S],S);stats=api('capture_wall_history_stats',[P,C.POINTER(Q)]);info=api('capture_layer_info',[P,C.POINTER(Q)]);bundle=api('capture_bundle',[P,Q,U,P,S],S)
# Independent NWH reader/address evaluator from existing component tests, without their main programs.
ns={'struct':struct}
for file,names in [('verify_compact_wall_history_host.py',{'parse'}),('test_bounded_wall_store_host.py',{'values'})]:
 tree=ast.parse((root/'work/android/capture'/file).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<independent-source-decoder>','exec'),ns)
proof_read=api('capture_write_ownership',[P,Q,U,U,U,P,S],S)
road_read=api('capture_road_history',[P,Q,U,U,U,P,S],S)
sky_enable=api('capture_sky_enable',[P,C.c_int]);bg_read=api('capture_background_scene',[P,Q,U,P,S],S);source_read=api('capture_source_world',[P,Q,U,U,U,P,S],S)
background_ready=0;selected_backgrounds={};rejected_backgrounds=[];last_background_key=None
road_checks=0;road_seen={};older_road_checks=0
proof_checks=0;proof_seen={};proof_older_checks=0
parse=ns['parse'];values=ns['values'];capture=json.loads((fixtures/'source-fixture-capture-report.json').read_text());expected={r['owner']['serial']:r for r in capture['road_records']};rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();h=op(os.fsencode(rom));assert h
seen={};verified=set();checks=old_checks=0;audiohash=hashlib.sha256();audioframes=0;pcm=(C.c_int16*8192)();last=None;peak=[0,0,0]
def snapshot(owner):
 epoch,serial,begin,end=owner;n=read(h,epoch,serial,begin,end,None,0);assert n,('Missing owner wall snapshot',owner);b=C.create_string_buffer(n);assert read(h,epoch,serial,begin,end,b,n)==n;return b.raw
def proof_snapshot(owner):
 n=proof_read(h,*owner,None,0);assert n==192080;b=C.create_string_buffer(n);assert proof_read(h,*owner,b,n)==n;return b.raw
def road_snapshot(owner):
 n=road_read(h,*owner,None,0);assert n>64;b=C.create_string_buffer(n);assert road_read(h,*owner,b,n)==n;return b.raw
def road_values(raw):
 h=struct.unpack_from('<8Q',raw);assert h[0]==0x3148524e and h[1]==1 and h[2]==len(raw);assets={};events=[];at=64
 while at<len(raw):
  tag,size=struct.unpack_from('<2Q',raw,at)
  if tag==1:
   a=struct.unpack_from('<8Q',raw,at);assert a[2]==len(assets)+1 and a[3]==1 and size==64+a[5];assets[a[2]]=(a[4],raw[at+64:at+size])
  else:
   assert tag==2 and size==164;e=struct.unpack_from('<12Q',raw,at);c=struct.unpack_from('<17I',raw,at+96);assert e[4] in assets and e[5]==0 and e[6]==assets[e[4]][0] and e[7]==1;events.append((e,c))
  at+=size
 assert at==len(raw) and len(assets)==h[4] and len(events)==h[5];state={}
 for e,c in events:
  data=assets[e[4]][1];u=c[8];v=c[9];offsets=[]
  for i in range(c[7]):
   u&=c[1];v&=c[2];offset=c[5]+2*((u>>16)+((v>>16)<<c[0]))-e[6];assert 0<=offset and offset+2<=len(data);offsets.append(offset);u=(u+c[10])&0xffffffff;v=(v+c[11])&0xffffffff
  for row in range(c[16]+1):
   for i,offset in enumerate(offsets):
    for lane in range(2):
     page,cell=divmod(c[6]+i*2+row*240+lane-0x06000000,0xa000)
     if page in (0,1) and cell<38400:state[(page,cell)]=(data[offset+lane],e[3])
 return state
try:
 assert not wall(h,1) and load(h,state,len(state)) and enable(h,1) and layers(h,1) and source(h,1) and wall(h,1) and wall(h,1) and sky_enable(h,1) and sky_enable(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0))==1
   assert C.string_at(pixels(h),153600)==oracle.read(153600),('Original image',i)
   t=(Q*4)();assert timing(h,t) and tuple(t[:2])==(16777216,280896) and t[2]==initial[2]+i+1 and t[3]==i+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    audioframes+=n;audiohash.update(C.string_at(pcm,n*4))
   st=(Q*8)();assert stats(h,st) and st[0]==1 and st[1]==0,('Wall failure',i,list(st));peak=[max(peak[j],st[j+4]) for j in range(3)]
   meta=(Q*5)()
   if not info(h,meta):continue
   bg_bytes=bg_read(h,meta[0],meta[1],None,0)
   if bg_bytes:background_ready+=1;last_background_key=(meta[0],meta[1])
   if meta[1] in capture['selected_refreshes']:
    key=str(meta[1])
    if bg_bytes:
     bg=C.create_string_buffer(bg_bytes);assert bg_read(h,meta[0],meta[1],bg,bg_bytes)==bg_bytes;entry=capture['fixtures'][key];(out/entry['filename']).write_bytes(bg.raw);selected_backgrounds[key]=entry['filename'];sentinel=C.create_string_buffer(b'unchanged');assert not bg_read(h,meta[0]+1,meta[1],sentinel,8) and not bg_read(h,meta[0],meta[1],sentinel,8) and sentinel.raw.startswith(b'unchanged')
    else:rejected_backgrounds.append(meta[1])
   n=bundle(h,meta[0],meta[1],None,0)
   if not n:continue
   b=C.create_string_buffer(n);assert bundle(h,meta[0],meta[1],b,n)==n;header=struct.unpack_from('<16Q',b.raw)
   for owner_index in range(header[7]):
    serial,begin,end,page=struct.unpack_from('<4I',b.raw,header[8+owner_index*2]+16);owner=(header[3],serial,begin,end)
    size=read(h,*owner,None,0)
    if not size:continue # Initial packet can precede first original wall submission.
    if owner in seen:
     if last and owner!=last:assert hashlib.sha256(snapshot(owner)).hexdigest()==seen[owner];old_checks+=1
     continue
    if last and read(h,*last,None,0):assert hashlib.sha256(snapshot(last)).hexdigest()==seen[last];old_checks+=1;assert hashlib.sha256(proof_snapshot(last)).hexdigest()==proof_seen[last];proof_older_checks+=1;assert hashlib.sha256(road_snapshot(last)).hexdigest()==road_seen[last];older_road_checks+=1
    road_raw=road_snapshot(owner);road_seen[owner]=hashlib.sha256(road_raw).hexdigest();proof_seen[owner]=hashlib.sha256(proof_snapshot(owner)).hexdigest();raw=snapshot(owner);digest=hashlib.sha256(raw).hexdigest();seen[owner]=digest;last=owner
    if serial in expected:
     record=expected[serial];proof_size=proof_read(h,*owner,None,0);assert proof_size==192080;proof_copy=C.create_string_buffer(proof_size);assert proof_read(h,*owner,proof_copy,proof_size)==proof_size;assert struct.unpack_from('<10Q',proof_copy.raw)==(0x3150524e,1,192080,owner[0],serial,begin,end,end+1,page,38400);expected_proof=(fixtures/record['provenance']['filename']).read_bytes();assert proof_copy.raw[80:]==expected_proof,('Original proof differs',serial);proof_checks+=38400;(out/f'owner-{serial}.nrp').write_bytes(proof_copy.raw);assert (begin,end,page)==tuple(record['owner'][k] for k in ('begin','end','page'));hh,a,e=parse(raw);assert hh[3]==header[3];wallstate=values(a,e);proof=(fixtures/record['provenance']['filename']).read_bytes();full=(fixtures/record['full_replay']['filename']).read_bytes()
     for cell in range(38400):
      if proof[cell]==2:assert wallstate[(page,cell)]==(full[cell],struct.unpack_from('<I',proof,38400+cell*4)[0]),(serial,cell);checks+=1
     nsp_bytes=source_read(h,*owner,None,0);assert nsp_bytes;nsp=C.create_string_buffer(nsp_bytes);assert source_read(h,*owner,nsp,nsp_bytes)==nsp_bytes;(out/f'source-{serial}.nsp').write_bytes(nsp.raw);(out/f'owner-{serial}.nwh').write_bytes(raw);(out/f'owner-{serial}.nrh').write_bytes(road_raw);road_state=road_values(road_raw)
     for cell in range(38400):
      if proof[cell]==1:assert road_state[(page,cell)]==(full[cell],struct.unpack_from('<I',proof,38400+cell*4)[0]),('Road source mismatch',serial,cell);road_checks+=1
     verified.add(serial)
    sentinel=C.create_string_buffer(b'unchanged');assert not read(h,header[3]+1,serial,begin,end,sentinel,8) and sentinel.raw.startswith(b'unchanged');assert not read(h,header[3],serial,begin+1,end,None,0);assert not read(h,*owner,sentinel,8) and sentinel.raw.startswith(b'unchanged');assert not road_read(h,header[3]+1,serial,begin,end,sentinel,8) and not road_read(h,header[3],serial,begin+1,end,None,0) and not road_read(h,*owner,sentinel,8) and sentinel.raw.startswith(b'unchanged');assert not proof_read(h,header[3]+1,serial,begin,end,sentinel,8) and not proof_read(h,header[3],serial,begin+1,end,None,0) and not proof_read(h,*owner,sentinel,8) and sentinel.raw.startswith(b'unchanged')
 assert verified==set(expected) and checks==299970,(verified,checks)
 assert audioframes==443007 and audiohash.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
 assert len(selected_backgrounds)==9 and len(set(rejected_backgrounds))==2,(selected_backgrounds,rejected_backgrounds);assert last and load(h,state,len(state));assert last_background_key and not bg_read(h,*last_background_key,None,0);assert not read(h,*last,None,0) and not proof_read(h,*last,None,0) and not road_read(h,*last,None,0);st=(Q*8)();assert stats(h,st) and st[0]==1 and st[1]==0 and st[2]!=last[0] and st[3]==0 and st[4]==0
 assert not read(h,*next(iter(seen)),None,0)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(80):assert step(h,1|(16 if 60<=i<120 else 0)) and C.string_at(pixels(h),153600)==oracle.read(153600)
 assert stats(h,st) and st[1]==0 and st[3]>0 and st[4]>0 and old_checks>100 and proof_older_checks==147 and older_road_checks==147 and road_checks==145665,(list(st),old_checks)
 assert sky_enable(h,0) and not bg_read(h,*last_background_key,None,0);assert wall(h,0) and not read(h,*last,None,0);assert wall(h,1);assert enable(h,0) and not read(h,*last,None,0)
finally:close(h)
report=dict(result='PASS_NORMAL_CORE_BACKGROUND_CAPTURE',background_snapshots=background_ready,selected_backgrounds=selected_backgrounds,rejected_warmup=sorted(set(rejected_backgrounds)),road_source_writer_checks=road_checks,older_road_checks=older_road_checks,proof_cells=proof_checks,older_proof_checks=proof_older_checks,original_frames=600,original_timing=True,audio_frames=audioframes,audio_sha256=audiohash.hexdigest(),wall_owners=len(seen),checked_owners=sorted(verified),source_writer_checks=checks,older_owner_immutable_checks=old_checks,peak_retained_events=peak[0],peak_assets=peak[1],peak_asset_bytes=peak[2],reset_disable_reenable_stale_guards=True,post_reset_original_frames=80,diagnostic_setup_required=False,android_runtime=False,live_renderer_connected=False)
(out/'background-owner-api-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
