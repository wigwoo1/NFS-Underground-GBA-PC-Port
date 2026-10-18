from pathlib import Path
import ctypes as C,os,json,hashlib,struct,zlib,threading,collections
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-store-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'store-build-report.json').read_text());assert build['dll_sha256']==sha(out/'recipe-store.dll')
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-store.dll'));core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(lib,name,args,r=I):f=getattr(lib,name);f.argtypes=args;f.restype=r;return f
minimum=fn(d,'nf_recipe_store_minimum',[],S)();op=fn(d,'nf_recipe_store_open',[Q,S],P);close=fn(d,'nf_recipe_store_close',[P],None);put=fn(d,'nf_recipe_store_put',[P,Q,U,Q,P,U]);prune=fn(d,'nf_recipe_store_prune',[P,Q,P,S]);reset=fn(d,'nf_recipe_store_reset',[P,Q]);info=fn(d,'nf_recipe_store_info',[P,P]);snap=fn(d,'nf_recipe_store_snapshot',[P,Q,P,S],P);free=fn(d,'nf_recipe_snapshot_free',[P],None);sinfo=fn(d,'nf_recipe_snapshot_info',[P,P]);writer=fn(d,'nf_recipe_snapshot_writer',[P,S,P]);block=fn(d,'nf_recipe_snapshot_block',[P,S,U,P,P])
def stats(pool):v=(Q*5)();assert info(pool,v);return tuple(v)
def keys(values):return (Q*(len(values)*2))(*(n for v in values for n in v))
def insert(pool,epoch,key,values):
 buffers=[C.create_string_buffer(v) for v in values];a=(Block*len(values))(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(buffers)]);return put(pool,epoch,*key,a,len(values))
def fingerprints(values):return tuple((len(v),hashlib.sha256(v).hexdigest()) for v in values)
validated_blocks=0

def check_snapshot(p,expected):
 global validated_blocks
 si=(Q*5)();assert sinfo(p,si) and si[1]==len(expected) and si[3]<=si[4]
 for index,(key,wanted) in enumerate(expected):
  wi=(Q*3)();assert writer(p,index,wi) and tuple(wi)==(*key,len(wanted))
  for b,want in enumerate(wanted):
   ptr=P();n=S();assert block(p,index,b,C.byref(ptr),C.byref(n)) and (n.value,hashlib.sha256(C.string_at(ptr,n.value)).hexdigest())==want;validated_blocks+=1
 return tuple(si)
# Budget rollback, immutable binding, input ownership and owner-thread guards.
assert not op(0,minimum) and not op(1,minimum-1)
p=op(1,minimum+100000);assert p;values=[b'original',b'shared'];assert insert(p,1,(1,1),values);s=stats(p);assert insert(p,1,(1,1),values) and stats(p)==s;assert not insert(p,1,(1,1),[b'changed']) and stats(p)==s
assert not insert(p,2,(1,2),values) and not insert(p,1,(3,2),values)
k=keys([(1,1)]);view=snap(p,1,k,1);assert view;expected=[((1,1),fingerprints(values))];check_snapshot(view,expected)
missing=keys([(2,999)]);assert not prune(p,1,missing,1) and not snap(p,1,missing,1) and stats(p)[1]==1
sentinel=P(123);n=S(456);assert not block(view,99,0,C.byref(sentinel),C.byref(n)) and (sentinel.value,n.value)==(123,456)
thread_result=[]
def rejected_worker():thread_result.extend([insert(p,1,(1,3),values),reset(p,2),prune(p,1,None,0),bool(snap(p,1,k,1))]);close(p)
t=threading.Thread(target=rejected_worker);t.start();t.join();assert thread_result==[0,0,0,False] and stats(p)[1]==1
assert prune(p,1,None,0) and stats(p)[1:3]==(0,0);check_snapshot(view,expected);assert reset(p,2) and not insert(p,1,(1,2),values);free(view);assert stats(p)[3]==minimum;close(p)
# Equal blocks in distinct writers must share immutable allocations.
p=op(1,minimum+100000);assert insert(p,1,(1,1),values) and insert(p,1,(2,1),values) and stats(p)[1:3]==(2,2)
v=snap(p,1,keys([(1,1),(2,1)]),2);assert v
pa=P();pb=P();na=S();nb=S();assert block(v,0,0,C.byref(pa),C.byref(na)) and block(v,1,0,C.byref(pb),C.byref(nb)) and pa.value==pb.value
free(v);close(p)
# Exact allocation boundary derived from actual reported allocation charge.
p=op(1,minimum+100000);assert insert(p,1,(1,1),[b'x']);charge=stats(p)[3]-minimum;close(p)
p=op(1,minimum+charge-1);before=stats(p);assert not insert(p,1,(1,1),[b'x']) and stats(p)==before;close(p)
p=op(1,minimum+charge);assert insert(p,1,(1,1),[b'x']);before=stats(p);assert not insert(p,1,(1,2),[b'x',b'z'*1000]) and stats(p)==before and not snap(p,1,keys([(1,1)]),1);close(p)
# Actual captured source inputs; all provenance reports/hashes are prerequisites.
road_dir=base/'NFSUG-pc-road-recipe-tests';wall_dir=base/'NFSUG-pc-wall-lineage-tests';rr=json.loads((road_dir/'recipe-test-report.json').read_text());wr=json.loads((wall_dir/'lineage-test-report.json').read_text());assert sha(road_dir/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(wall_dir/'wall-source-lineage.wclz')==wr['archive_sha256'];assert rr['rom_state_sha256']==wr['rom_state_sha256']
road=collections.defaultdict(list);raw=(road_dir/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(raw):
 length=struct.unpack_from('<I',raw,at)[0];at+=4;record=zlib.decompress(raw[at:at+length]);at+=length;h=struct.unpack_from('<10Q',record);pos=80+h[5]*68;blocks=[]
 for i in range(12):size=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks.append(record[pos:pos+size]);pos+=size
 size=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks+=[record[pos:pos+size],record[80:80+h[5]*68],record[:80]];assert pos+size==len(record);road[h[3]].append((h,blocks))
wall=(wall_dir/'wall-source-lineage.wclz').read_bytes();wall_at=8;wall_calls={}
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
co=fn(core,'nfa_core_open',[C.c_char_p],P);cl=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rc=fn(reader,'nf_pc_source_reader_close',[P],None);fi=fn(reader,'nf_pc_source_frame_info',[P,P]);oi=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ff=fn(reader,'nf_pc_source_frame_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';unchanged={str(v):sha(v) for v in [rom,state]};state_data=state.read_bytes();h=co(os.fsencode(rom));assert h and load(h,state_data,len(state_data))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=ro(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial)
epoch=next(iter(road.values()))[0][0][2];pool=op(epoch,64*1024*1024);assert pool;expected={};insertions=0;peak=minimum;pruned=0;snapshot_rows=[];split_scenes=0;held=None;held_expected=None;last_view=None;last_expected=None;targets={int(v.stem) for v in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')}|{11879};pcm=(C.c_int16*8192)();samples=0;digest=hashlib.sha256()
def add(key,refresh,values):
 global insertions,peak
 assert key not in expected and insert(pool,epoch,key,values),('Store insert failed',key,stats(pool));expected[key]=(refresh,fingerprints(values));insertions+=1
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   for header,blocks in road.get(tick[2]-1,[]):
    assert header[2]==epoch
    for run in range(header[5]):add((1,header[4]+run),header[3],blocks)
   length=struct.unpack_from('<I',wall,wall_at)[0];wall_at+=4;blob=zlib.decompress(wall[wall_at:wall_at+length]);wall_at+=length;pos=0
   while pos<len(blob):
    tag,size,wall_epoch,refresh,call=struct.unpack_from('<5Q',blob,pos);assert wall_epoch==epoch;record=blob[pos:pos+size]
    if tag==2:
     cursor=64;blocks=[]
     for b in range(12):n=struct.unpack_from('<I',record,cursor)[0];cursor+=4;blocks.append(record[cursor:cursor+n]);cursor+=n
     assert cursor==len(record);wall_calls[call]=(blocks,record[:64])
    elif tag==3:
     header=struct.unpack_from('<10Q',record);blocks,meta=wall_calls[call];add((2,header[5]),refresh,blocks+[record[80:160],record[160:] or b'\0',meta])
    elif tag==4:wall_calls.pop(call)
    else:assert tag==1
    pos+=size
   peak=max(peak,stats(pool)[3])
   if tick[2] in targets or index==599:
    frame=capture(r,64*1024*1024);assert frame;meta=(Q*8)();assert fi(frame,meta);split_scenes+=meta[4]==2;wanted=set();newest=0
    try:
     for owner in range(meta[4]):
      owner_key=(Q*5)();assert oi(frame,owner,owner_key) and owner_key[0]==epoch;newest=max(newest,owner_key[3])
      for kind,which in [(1,2),(2,3)]:
       ptr=P();n=S();assert component(frame,owner,which,C.byref(ptr),C.byref(n));history=C.string_at(ptr,n.value);cursor=64
       while cursor<len(history):
        tag,size=struct.unpack_from('<2Q',history,cursor)
        if tag==2:wanted.add((kind,struct.unpack_from('<Q',history,cursor+16)[0]))
        cursor+=size
       assert cursor==len(history)
    finally:ff(frame)
    ordered=sorted(wanted);k=keys(ordered);view=snap(pool,epoch,k,len(ordered));assert view;wanted_values=[(key,expected[key][1]) for key in ordered];check_snapshot(view,wanted_values)
    keep=wanted|{key for key,(refresh,_) in expected.items() if refresh>newest};before_count=len(expected);assert prune(pool,epoch,keys(sorted(keep)),len(keep));expected={key:value for key,value in expected.items() if key in keep};pruned+=before_count-len(expected);assert stats(pool)[1]==len(expected);check_snapshot(view,wanted_values)
    if held is None:held=view;held_expected=wanted_values
    elif index==599:last_view=view;last_expected=wanted_values
    else:free(view)
    if held:check_snapshot(held,held_expected)
    st=stats(pool);peak=max(peak,st[3]);snapshot_rows.append(dict(logic_refresh_counter=tick[2],source_refresh=meta[1],owners=meta[4],published_writers=len(ordered),pending_or_retained_writers=st[1],interned_blocks=st[2],accounted_bytes=st[3],removed=before_count-len(expected)))
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
 assert wall_at==len(wall) and not wall_calls and insertions==rr['road_runs']+wr['columns'] and len(snapshot_rows)==11 and split_scenes>0 and pruned>0, (wall_at,len(wall),len(wall_calls),insertions,rr['road_runs']+wr['columns'],len(snapshot_rows),split_scenes,pruned)
 assert reset(pool,epoch+1) and stats(pool)[1:3]==(0,0) and not snap(pool,epoch,keys([(1,1)]),1);check_snapshot(held,held_expected);check_snapshot(last_view,last_expected)
 # One published frame remains valid after owner store/core shutdown; read/free on worker.
 free(held);held=None;close(pool);pool=None;rc(r);r=None;cl(h);h=None
 result=[]
 def worker():check_snapshot(last_view,last_expected);free(last_view);result.append(True)
 thread=threading.Thread(target=worker);thread.start();thread.join();assert result==[True];last_view=None
finally:
 if held:free(held)
 if last_view:free(last_view)
 if pool:close(pool)
 if r:rc(r)
 if h:cl(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' and unchanged=={str(v):sha(v) for v in [rom,state]}
report=dict(result='PASS_BOUNDED_OWNED_ROAD_WALL_RECIPE_STORE',inserted_writers=insertions,pruned_writers=pruned,published_scenes=len(snapshot_rows),split_owner_scenes=split_scenes,validated_blocks=validated_blocks,maximum_accounted_bytes=peak,budget_bytes=64*1024*1024,exact_budget_boundary_and_atomic_failure=True,shared_block_interning=True,stale_epoch_rejected=True,snapshot_survives_prune_reset_store_and_core_close=True,snapshot_read_and_freed_on_worker=True,store_wrong_thread_rejected=True,original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,no_extra_logic_steps=True,rom_state_sha256=unchanged,road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],dll_sha256=sha(out/'recipe-store.dll'),build_report_sha256=sha(out/'store-build-report.json'),script_sha256=sha(Path(__file__)),rows=snapshot_rows,live_capture_integration=False,fractional_motion=False,full_scene_60fps=False,scope='Store fed previously verified source archives at original refreshes; prune keys from eleven actual retained road/wall scene snapshots including split owners plus unpublished newer writes. No live producer hookup or fractional renderer integration.')
(out/'store-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
