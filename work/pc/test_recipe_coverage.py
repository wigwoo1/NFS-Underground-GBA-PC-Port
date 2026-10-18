from pathlib import Path
import os,ctypes as C,json,hashlib,struct,threading,zlib,collections
import numpy as np
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-coverage-tests';runtime=base/'NFSUG-pc-recipe-runtime-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'coverage-build-report.json').read_text());assert sha(out/'recipe-coverage.dll')==build['dll_sha256']
for p,h in build['source_sha256'].items():assert sha(p)==h,p
rb=json.loads((runtime/'live-recipe-build-report.json').read_text());assert sha(runtime/'capture-host.dll')==rb['core_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(runtime/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'));cov=C.CDLL(str(out/'recipe-coverage.dll'));old=C.CDLL(str(base/'NFSUG-pc-retention-tests/source-retention.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,res=I):f=getattr(lib,name);f.argtypes=args;f.restype=res;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);acquire=fn(d,'nf_pc_live_recipe_acquire',[P],P);sinfo=fn(d,'nf_recipe_snapshot_info',[P,P]);writer=fn(d,'nf_recipe_snapshot_writer',[P,S,P]);block=fn(d,'nf_recipe_snapshot_block',[P,S,U,P,P]);sf=fn(d,'nf_recipe_snapshot_free',[P],None);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rc=fn(reader,'nf_pc_source_reader_close',[P],None);fi=fn(reader,'nf_pc_source_frame_info',[P,P]);oi=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ff=fn(reader,'nf_pc_source_frame_free',[P],None)
decode=fn(cov,'nf_pc_recipe_coverage_decode',[P,S,P,S,P,U,U,U,S],P);free=fn(cov,'nf_pc_recipe_coverage_free',[P],None);info=fn(cov,'nf_pc_recipe_coverage_info',[P,P]);buffer=fn(cov,'nf_pc_recipe_coverage_buffer',[P,U,P,P]);olddecode=fn(old,'nf_pc_retention_decode',[P,S,P,S,P,U,U,U,S],P);oldfree=fn(old,'nf_pc_retention_free',[P],None);oldbuf=fn(old,'nf_pc_retention_buffer',[P,U,P,P])
def blob(func,*args):p=P();n=S();assert func(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def independent(history,proof,key,kind,top,bottom):
 assets={};ids=np.zeros(38400,np.uint64);indices=np.zeros(38400,np.uint8);refreshes=np.zeros(38400,np.uint32);events={};pos=64;baseaddr=0x06000000+key[4]*0xa000
 def put(address,ordinal,refresh,index):
  cell=(address&0xffffffff)-baseaddr
  if 0<=cell<38400:ids[cell]=ordinal;indices[cell]=index;refreshes[cell]=refresh
 while pos<len(history):
  tag,size=struct.unpack_from('<2Q',history,pos);rec=history[pos:pos+size]
  if tag==1:
   _,_,aid,category,address,length=struct.unpack_from('<6Q',rec);assets[aid]=(address,rec[64:64+length])
  else:
   fields=struct.unpack_from('<12Q',rec);ordinal,refresh,aid,shade=fields[2:6];cmd=struct.unpack('<'+str(17 if kind==2 else 20)+'I',rec[96:]);events[ordinal]=(refresh,rec[96:])
   if refresh<=key[3]:
    address,tex=assets[aid]
    if kind==2:
     shift,um,vm=cmd[:3];u,v=cmd[8:10];du,dv=cmd[10:12]
     for k in range(cmd[7]):
      uu=((u+k*du)&0xffffffff)&um;vv=((v+k*dv)&0xffffffff)&vm;offset=cmd[5]+2*((uu>>16)+((vv>>16)<<shift))-address
      for duplicate in range(cmd[16]+1):
       for lane in range(2):put(cmd[6]+k*2+duplicate*240+lane,ordinal,refresh,tex[offset+lane])
    else:
     shift=cmd[3];uvshift=15;texture=cmd[9];delta=cmd[11];stride=cmd[2];vertical=cmd[18];mask=((cmd[4]<<15)-1)&0xffffffff
     if cmd[6] and delta>0x1b000:shift-=2;uvshift=17;texture=(texture+cmd[7])&0xffffffff
     texture=((texture+((cmd[13]&cmd[16])>>uvshift))&0xffffffff)&~1;dest=(cmd[17]+((stride*(cmd[1]>>14))<<1))&0xffffffff
     for row in range(cmd[19]):
      value=vertical&mask;offset=((texture+((value>>uvshift)<<shift))&0xffffffff)-address;index=tex[offset]
      if index:
       mapped=assets[shade][1][index*16] if shade else index
       for lane in range(2):put((dest&~1)+lane,ordinal,refresh,mapped)
      dest=(dest+(stride<<1))&0xffffffff;vertical=(vertical+delta)&0xffffffff
  pos+=size
 assert pos==len(history)
 owned=np.frombuffer(proof,np.uint8,count=38400,offset=80)==(1 if kind==2 else 2);ys=np.arange(38400)//240;owned&=(ys>=top)&(ys<bottom);cells=np.nonzero(owned)[0];assert (ids[cells]>0).all();outrows=np.column_stack([cells,np.full(len(cells),key[0]),np.full(len(cells),kind-1),ids[cells],refreshes[cells],indices[cells]]).astype('<u8');return outrows,events
# Source-call capture and accepted column timestamps can legitimately differ.
wall_dir=base/'NFSUG-pc-wall-lineage-tests';wall_report=json.loads((wall_dir/'lineage-test-report.json').read_text());assert sha(wall_dir/'wall-source-lineage.wclz')==wall_report['archive_sha256']
raw=(wall_dir/'wall-source-lineage.wclz').read_bytes();at=8;calls={};wall_times={};archive_wall_deltas=collections.Counter();covered_wall_deltas=collections.Counter()
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;data=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(data):
  tag,n,epoch,refresh,call=struct.unpack_from('<5Q',data,pos)
  if tag==2:calls[call]=refresh
  elif tag==3:
   ordinal=struct.unpack_from('<Q',data,pos+40)[0];wall_times[ordinal]=(calls[call],refresh);archive_wall_deltas[refresh-calls[call]]+=1
  elif tag==4:calls.pop(call)
  pos+=n
assert not calls and len(wall_times)==27027
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';unchanged={str(p):sha(p) for p in [rom,state]};saved=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,saved,len(saved))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));readerh=ro(C.byref(api),64*1024*1024);assert readerh;initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;targets={int(p.stem) for p in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')}|{11879,12435};rows=[];held=[];cells_checked=unique_bindings=split=negative=older_cells=0;max_age=0;fixture_hashes={}
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   if tick[2] not in targets and index!=599:continue
   frame=capture(readerh,64*1024*1024);assert frame;meta=(Q*8)();assert fi(frame,meta);split+=int(meta[4]==2)
   try:
    for owner in range(meta[4]):
     key=(Q*5)();assert oi(frame,owner,key);view=acquire(key);assert view;si=(Q*5)();assert sinfo(view,si) and si[0]==key[0];lookup={}
     try:
      for wi in range(si[1]):
       data=(Q*3)();assert writer(view,wi,data);lookup[tuple(data[:2])]=wi
      for kind in [2,3]:
       history=blob(component,frame,owner,kind);proof=blob(component,frame,owner,4);top=meta[3] if owner else 0;bottom=160 if meta[4]==1 or owner else meta[3];coverage=decode(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert coverage,(list(key),kind);oldh=olddecode(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert oldh
       try:
        mi=(Q*10)();assert info(coverage,mi);assert blob(buffer,coverage,0)==blob(oldbuf,oldh,0) and blob(buffer,coverage,1)==blob(oldbuf,oldh,1)
        actual=blob(buffer,coverage,2);records=np.frombuffer(actual,dtype='<u8').reshape(-1,6);expected,events=independent(history,proof,key,kind,top,bottom);assert np.array_equal(records,expected),('Writer oracle mismatch',list(key),kind);cells_checked+=len(records);age=key[3]-records[:,4];older_cells+=int(np.count_nonzero(age));max_age=max(max_age,int(age.max()) if len(age) else 0)
        ordinalset=set(map(int,records[:,3]));unique_bindings+=len(ordinalset)
        for ordinal in ordinalset:
         sourcekind=kind-1;wi=lookup[(sourcekind,ordinal)];header=blob(block,view,wi,14);epoch,refresh=struct.unpack_from('<2Q',header,16);assert epoch==key[0]
         if kind==2:assert refresh==events[ordinal][0]
         else:assert (refresh,events[ordinal][0])==wall_times[ordinal];covered_wall_deltas[events[ordinal][0]-refresh]+=1
         if kind==2:
          first,count=struct.unpack_from('<2Q',header,32);commands=blob(block,view,wi,13);assert first<=ordinal<first+count and commands[(ordinal-first)*68:(ordinal-first+1)*68]==events[ordinal][1]
         else:assert blob(block,view,wi,12)==events[ordinal][1]
        rows.append(dict(owner=list(key),kind=kind,cells=len(records),source_writers=len(ordinalset),older_cells=int(np.count_nonzero(age)),maximum_age=int(age.max()) if len(age) else 0,bytes=mi[9]));print('PASS',key[1],kind,len(records),'writers',len(ordinalset),flush=True)
        if negative==0:
         assert not decode(history,len(history),proof,len(proof),key,kind,top,bottom,mi[9]-1);exact=decode(history,len(history),proof,len(proof),key,kind,top,bottom,mi[9]);assert exact;free(exact);negative+=1
         bad=(Q*5)(*key);bad[0]+=1;assert not decode(history,len(history),proof,len(proof),bad,kind,top,bottom,mi[9]);negative+=1
         p=P(123);n=S(456);assert not buffer(coverage,3,C.byref(p),C.byref(n)) and (p.value,n.value)==(123,456);negative+=1
         badhistory=bytearray(history);pos=64
         while struct.unpack_from('<Q',badhistory,pos)[0]!=2:pos+=struct.unpack_from('<Q',badhistory,pos+8)[0]
         struct.pack_into('<Q',badhistory,pos+16,0);assert not decode(bytes(badhistory),len(badhistory),proof,len(proof),key,kind,top,bottom,mi[9]);negative+=1
         hb=C.create_string_buffer(history);pr=C.create_string_buffer(proof);copy=decode(hb,len(history),pr,len(proof),key,kind,top,bottom,mi[9]);assert copy;C.memset(hb,0,len(history));C.memset(pr,0,len(proof));assert blob(buffer,copy,2)==actual;free(copy);negative+=1
        if index==599 or key[1]==146:
         path=out/('owner-'+str(key[1])+'-'+str(kind)+'.nccz');payload=struct.pack('<5Q4I',*key,kind,top,bottom,len(history))+history+proof;path.write_bytes(b'NCCZ\x01\0\0\0'+zlib.compress(payload));fixture_hashes[path.name]=sha(path)
        held.append((coverage,hashlib.sha256(actual).hexdigest()));coverage=None
       finally:
        oldfree(oldh)
        if coverage:free(coverage)
     finally:sf(view)
   finally:ff(frame)
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
finally:rc(readerh);close(h)
worker_result=[]
def worker():
 for coverage,want in held:assert hashlib.sha256(blob(buffer,coverage,2)).hexdigest()==want;free(coverage)
 worker_result.append(True)
t=threading.Thread(target=worker);t.start();t.join();assert worker_result==[True]
assert split and cells_checked and unique_bindings and samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' and unchanged=={str(p):sha(p) for p in [rom,state]}
r=dict(result='PASS_RETAINED_CELLS_EXACT_SOURCE_WRITER_BINDINGS',cases=len(rows),cells_checked=cells_checked,unique_writer_bindings_checked=unique_bindings,split_frames=split,older_retained_cells=older_cells,maximum_source_age_refreshes=max_age,baseline_indices_and_records_exact=True,independent_python_ordinal_oracle_exact=True,all_covered_writer_keys_and_original_commands_match_snapshots=True,negative_budget_owner_buffer_history_lifetime_checks=negative,coverage_survives_input_frame_snapshot_core_close_and_worker_read_free=True,original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,no_getter_logic_steps=True,rom_state_sha256=unchanged,dll_sha256=sha(out/'recipe-coverage.dll'),build_report_sha256=sha(out/'coverage-build-report.json'),core_sha256=sha(runtime/'capture-host.dll'),script_sha256=sha(Path(__file__)),fixture_sha256=fixture_hashes,rows=rows,archive_wall_capture_to_write_deltas=dict(archive_wall_deltas),covered_wall_capture_to_write_deltas=dict(covered_wall_deltas),wall_archive_sha256=wall_report['archive_sha256'],scope='Exact original retained cells to original accepted writer keys; no inferred screen-shape identities and no world coverage reprojection.',live_host_integration=False,full_scene_60fps=False)
(out/'coverage-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['rows','rom_state_sha256']},indent=2))
