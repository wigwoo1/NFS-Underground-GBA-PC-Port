from pathlib import Path
import os,ctypes as C,json,hashlib,struct,zlib,threading,time
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');parser=__import__('argparse').ArgumentParser();parser.add_argument('--output-dir',type=Path,default=base/'NFSUG-pc-live-recipe-tests');out=parser.parse_args().output_dir
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-recipe-build-report.json').read_text());assert sha(out/'capture-host.dll')==build['core_sha256']
road_dir=base/'NFSUG-pc-road-recipe-tests';wall_dir=base/'NFSUG-pc-wall-lineage-tests';rr=json.loads((road_dir/'recipe-test-report.json').read_text());wr=json.loads((wall_dir/'lineage-test-report.json').read_text());assert sha(road_dir/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(wall_dir/'wall-source-lineage.wclz')==wr['archive_sha256']
def fps(values):return tuple((len(v),hashlib.sha256(v).hexdigest()) for v in values)
expected={};road=(road_dir/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(road):
 n=struct.unpack_from('<I',road,at)[0];at+=4;record=zlib.decompress(road[at:at+n]);at+=n;h=struct.unpack_from('<10Q',record);pos=80+h[5]*68;blocks=[]
 for i in range(12):size=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks.append(record[pos:pos+size]);pos+=size
 size=struct.unpack_from('<I',record,pos)[0];pos+=4;values=fps(blocks+[record[pos:pos+size],record[80:80+h[5]*68],record[:80]])
 for i in range(h[5]):expected[(1,h[4]+i)]=values
wall=(wall_dir/'wall-source-lineage.wclz').read_bytes();at=8;calls={}
while at<len(wall):
 n=struct.unpack_from('<I',wall,at)[0];at+=4;blob=zlib.decompress(wall[at:at+n]);at+=n;pos=0
 while pos<len(blob):
  tag,size,epoch,refresh,call=struct.unpack_from('<5Q',blob,pos);record=blob[pos:pos+size]
  if tag==2:
   cursor=64;blocks=[]
   for i in range(12):n=struct.unpack_from('<I',record,cursor)[0];cursor+=4;blocks.append(record[cursor:cursor+n]);cursor+=n
   calls[call]=(fps(blocks),record[:64])
  elif tag==3:
   header=struct.unpack_from('<10Q',record);values,meta=calls[call];expected[(2,header[5])]=values+fps([record[80:160],record[160:] or b'\0',meta])
  elif tag==4:calls.pop(call)
  pos+=size
assert len(expected)==rr['road_runs']+wr['columns'] and not calls
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(name,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,r=I):f=getattr(lib,name);f.argtypes=args;f.restype=r;return f
op=fn(d,'nfa_core_open',[C.c_char_p],P);close=fn(d,'nfa_core_close',[P],None);load=fn(d,'nfa_core_load_state',[P,P,S]);step=fn(d,'nfa_core_step',[P,U]);pixels=fn(d,'nfa_core_pixels',[P],P);audio=fn(d,'nfa_core_read_audio',[P,P,S],S);timing=fn(d,'nfa_core_timing',[P,P]);status=fn(d,'nf_pc_live_recipe_info',[P]);acquire=fn(d,'nf_pc_live_recipe_acquire',[P],P);sinfo=fn(d,'nf_recipe_snapshot_info',[P,P]);writer=fn(d,'nf_recipe_snapshot_writer',[P,S,P]);block=fn(d,'nf_recipe_snapshot_block',[P,S,U,P,P]);free=fn(d,'nf_recipe_snapshot_free',[P],None);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rc=fn(reader,'nf_pc_source_reader_close',[P],None);fi=fn(reader,'nf_pc_source_frame_info',[P,P]);oi=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ff=fn(reader,'nf_pc_source_frame_free',[P],None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';unchanged={str(v):sha(v) for v in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(d,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(d,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=ro(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=checked=owners=split=0;rows=[];held=None;held_key=None;last=None;last_key=None;costs=[];targets={int(p.stem) for p in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')}|{11879}
def validate(view,wanted=None):
 global checked
 si=(Q*5)();assert sinfo(view,si) and si[3]<=si[4];actual=set()
 for i in range(si[1]):
  wi=(Q*3)();assert writer(view,i,wi);key=tuple(wi[:2]);assert key not in actual and key in expected and wi[2]==len(expected[key]);actual.add(key)
  for b,want in enumerate(expected[key]):
   p=P();n=S();assert block(view,i,b,C.byref(p),C.byref(n)) and (n.value,hashlib.sha256(C.string_at(p,n.value)).hexdigest())==want,('Archived source mismatch',key,b);checked+=1
 if wanted is not None:assert actual==wanted,(len(actual),len(wanted),list(actual^wanted)[:5])
 return actual
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   began=time.perf_counter();assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;costs.append((time.perf_counter()-began)*1000);assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   st=(Q*11)()
   if status(st):
    if st[1]:(out/'failed-live-status.json').write_text(json.dumps(dict(index=index,timing=list(tick),status=list(st)),indent=2));raise AssertionError(('Direct capture rejected',index,list(st)))
   if tick[2] in targets or index==599:
    frame=capture(r,64*1024*1024);assert frame;meta=(Q*8)();assert fi(frame,meta);split+=meta[4]==2
    try:
     for owner in range(meta[4]):
      key=(Q*5)();assert oi(frame,owner,key);wanted=set()
      for kind,which in [(1,2),(2,3)]:
       p=P();n=S();assert component(frame,owner,which,C.byref(p),C.byref(n));raw=C.string_at(p,n.value);at=64
       while at<len(raw):
        tag,size=struct.unpack_from('<2Q',raw,at)
        if tag==2:wanted.add((kind,struct.unpack_from('<Q',raw,at+16)[0]))
        at+=size
       assert at==len(raw)
      view=acquire(key);assert view,('Owner lookup failed',list(key),list(st));validate(view,wanted);owners+=1
      if held is None:held=view;held_key=tuple(key)
      elif index==599:last=view;last_key=tuple(key)
      else:free(view)
      rows.append(dict(logic_counter=tick[2],source_refresh=meta[1],owner=list(key),writers=len(wanted)))
    finally:ff(frame)
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
  assert status(st) and not st[1] and st[2:4]==[rr['road_runs'],wr['columns']] and st[4]>100 and not st[10] and split>0
  for field in range(5):bad=(Q*5)(*last_key);bad[field]+=1;assert not acquire(bad)
  results=[]
  def wrong_thread():results.append(bool(acquire((Q*5)(*last_key))))
  t=threading.Thread(target=wrong_thread);t.start();t.join();assert results==[False]
  validate(held);assert load(h,data,len(data)) and not acquire((Q*5)(*last_key));validate(held);validate(last)
finally:
 rc(r);close(h)
# The core and owner store no longer exist; snapshots are still independent.
validate(held);free(held);worker_result=[]
def worker():validate(last);free(last);worker_result.append(True)
t=threading.Thread(target=worker);t.start();t.join();assert worker_result==[True]
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e' and unchanged=={str(v):sha(v) for v in [rom,state]}
report=dict(result='PASS_DIRECT_CAPTURE_OWNED_ROAD_WALL_RECIPES',road_writers=st[2],wall_writers=st[3],completed_owner_snapshots=st[4],selected_owner_acquisitions=owners,split_scenes=split,validated_blocks=checked,final_pool_writers=st[5],final_interned_blocks=st[6],peak_accounted_store_bytes=st[8],budget_bytes=st[9],capture_step_mean_ms=sum(costs)/len(costs),capture_step_max_ms=max(costs),archive_blocks_exact=True,reset_stale_key_rejected=True,all_owner_fields_checked=True,owner_acquire_wrong_thread_rejected=True,snapshots_survive_reset_core_and_store_close=True,snapshot_read_free_on_worker=True,original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,no_extra_logic_steps=True,rom_state_sha256=unchanged,core_sha256=sha(out/'capture-host.dll'),build_report_sha256=sha(out/'live-recipe-build-report.json'),script_sha256=sha(Path(__file__)),road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],rows=rows,playable_host_integration=False,fractional_motion=False,full_scene_60fps=False,scope='Direct original capture callbacks populate native store and snapshot/prune at every owner close. Selected snapshots compare all blocks to independent prior archives. Wall-clock step costs are diagnostic, not a verified presentation or gameplay rate.')
(out/'live-recipe-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
