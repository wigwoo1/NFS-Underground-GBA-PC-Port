from pathlib import Path
import ctypes as C,os,json,hashlib,threading
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-native-scene-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
with os.add_dll_directory('C:/msys64/mingw64/bin'):lib=C.CDLL(str(out/'recipe-gpu.dll'))
def bind(d,name,args,res=C.c_int):f=getattr(d,name);f.argtypes=args;f.restype=res;return f
prepare=bind(lib,'nf_pc_writer_native_scene_prepare',[P,P,S],P);free=bind(lib,'nf_pc_writer_native_scene_free',[P],None);info=bind(lib,'nf_pc_writer_native_scene_info',[P,P]);draw=bind(lib,'nf_pc_writer_native_scene_draw',[P,P,U,U,U,U,P,S]);render=bind(lib,'nf_pc_writer_native_scene_render',[P,P,U,U,U,U]);open_gpu=bind(lib,'nf_pc_scene_gpu_open',[],P);close_gpu=bind(lib,'nf_pc_scene_gpu_close',[P],None);read=bind(lib,'nf_pc_scene_gpu_read_target',[P,P,S]);store_open=bind(lib,'nf_recipe_store_open',[Q,S],P);store_close=bind(lib,'nf_recipe_store_close',[P],None);snapshot=bind(lib,'nf_recipe_store_snapshot',[P,Q,P,S],P);snapfree=bind(lib,'nf_recipe_snapshot_free',[P],None)
cap={};prepared=[];guards=0

def capture_native(frame,scene,meta):
 global guards
 if meta[1] not in [12434,12437,12438]:return
 core=cap['core'];acquire=bind(core,'nf_pc_live_recipe_acquire',[P],P);drop=bind(core,'nf_recipe_snapshot_free',[P],None);views=(P*2)();held=[]
 try:
  for owner in range(meta[4]):key=(Q*5)();assert cap['oi'](frame,owner,key);view=acquire(key);assert view;views[owner]=view;held.append(view)
  result=[]
  def worker():result.append(prepare(frame,views,64*1024*1024))
  t=threading.Thread(target=worker);t.start();t.join();assert len(result)==1 and result[0],('Native worker preparation failed',list(meta));obj=result[0];stats=(Q*10)();assert info(obj,stats) and stats[8]<=stats[9]<=64*1024*1024;prepared.append((obj,list(stats)))
  assert not prepare(None,views,64*1024*1024);assert not prepare(frame,None,64*1024*1024);assert not prepare(frame,views,1);guards+=3
  if len(prepared)==1:
   exact=prepare(frame,views,stats[9]);assert exact;ei=(Q*10)();assert info(exact,ei) and list(ei)==list(stats);free(exact);assert not prepare(frame,views,stats[9]-1);guards+=1
   empty_store=store_open(meta[0],64*1024*1024);empty=snapshot(empty_store,meta[0],None,0);assert empty;bad=(P*2)(*views);bad[0]=empty;assert not prepare(frame,bad,64*1024*1024);snapfree(empty);store_close(empty_store);guards+=1
   class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
   entry=(Q*3)();assert bind(core,'nf_recipe_snapshot_writer',[P,S,P])(views[0],0,entry);blocks=(Block*15)()
   for j in range(15):assert bind(core,'nf_recipe_snapshot_block',[P,S,U,P,P])(views[0],0,j,C.byref(blocks[j],Block.data.offset),C.byref(blocks[j],Block.bytes.offset))
   dup_store=store_open(meta[0],64*1024*1024);assert dup_store and bind(lib,'nf_recipe_store_put',[P,Q,U,Q,P,U])(dup_store,meta[0],entry[0],entry[1],blocks,15);dup=snapshot(dup_store,meta[0],(Q*4)(entry[0],entry[1],entry[0],entry[1]),2);assert dup;bad[0]=dup;assert not prepare(frame,bad,64*1024*1024);snapfree(dup);store_close(dup_store);guards+=1
   wrong_store=store_open(meta[0]+1,64*1024*1024);wrong=snapshot(wrong_store,meta[0]+1,None,0);assert wrong;bad[0]=wrong;assert not prepare(frame,bad,64*1024*1024);snapfree(wrong);store_close(wrong_store);guards+=1
  print('NATIVE_OWNED_SCENE_PREPARED',list(stats),flush=True)
 finally:
  for view in held:drop(view)
original=here/'test_writer_scene_gpu.py';prefix=original.read_text().split("original=here/'test_writer_gpu.py'")[0].replace('NFSUG-pc-writer-scene-tests','NFSUG-pc-writer-native-scene-tests');anchor='assert scene;scenes.append(scene)';assert prefix.count(anchor)==1;prefix=prefix.replace(anchor,anchor+';capture_native(f,scene,meta)');cap.update(__file__=str(original),__name__='native_scene_capture',capture_native=capture_native)
try:
 exec(compile(prefix,str(original),'exec'),cap);assert len(prepared)==3
 # At this point every input core recipe view/frame/reader/core has been freed.
 g=open_gpu();assert g;rows=[];images={};prior=base/'NFSUG-pc-writer-composition-tests'
 try:
  for obj,stats in prepared:
   expected_png=np.array(Image.open(prior/('complete-source-writers-'+str(stats[1])+'-4k.png')))[::-1].copy()
   for width,height,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
    buf=C.create_string_buffer(width*height*4);again=C.create_string_buffer(len(buf));assert draw(g,obj,width,height,aw,ah,buf,len(buf));assert render(g,obj,width,height,aw,ah) and read(g,again,len(again)) and buf.raw==again.raw
    if width==3840:
     actual=np.frombuffer(buf.raw,np.uint8).reshape(height,width,4);assert np.array_equal(actual,expected_png),('Native scene differs',stats[1],int(np.any(actual!=expected_png,axis=2).sum()));path=out/('native-owned-'+str(stats[1])+'-4k.png');Image.fromarray(actual[::-1]).save(path);images[path.name]=sha(path)
    else:
     # Original-resolution comparison uses the immutable captured baseline scene,
     # whose lifetime is independent of the new native object.
     scene=next(s for s in cap['scenes'] if bind(lib,'nf_pc_scene_info',[P,P])(s,(v:=(Q*8)())) and v[1]==stats[1]);assert bind(lib,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S])(g,scene,width,height,aw,ah,again,len(again)) and buf.raw==again.raw
    rows.append(dict(refresh=stats[1],size=[width,height,aw,ah],native_info=stats,pixel_differences=0));print('NATIVE_SCENE_GPU_PASS',stats[1],width,flush=True)
 finally:close_gpu(g)
finally:
 freed=[]
 def free_worker():
  for obj,expected in prepared:
   stats=(Q*10)();assert info(obj,stats) and list(stats)==expected;free(obj);freed.append(obj)
 t=threading.Thread(target=free_worker);t.start();t.join();assert len(freed)==len(prepared)
 for s in cap.get('scenes',[]):cap['sf'](s)
r=dict(result='PASS_NATIVE_WORKER_OWNED_COMPLETE_ENDPOINT_SCENES',cases=len(rows),rows=rows,pixel_differences=0,negative_requests=guards,exact_constructor_peak_budget_accepts=True,one_byte_less_rejects=True,worker_prepare_and_worker_read_free=True,input_recipe_views_frames_reader_core_closed_before_gpu=True,gpu_only_render_matches_readback=True,original_replay_frames_exact=600,audio_frames=cap['samples'],audio_sha256=cap['digest'].hexdigest(),rom_state_unchanged=cap['unchanged'],diagnostic_images=images,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),script_sha256=sha(Path(__file__)),capture_source_sha256=sha(original),executed_capture_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),full_scene_60fps=False,live_integration=False,scope='Native owned endpoint preparation from captured immutable frame/core recipe views; combined published/constructor retained budget excludes existing bounded decode/partition/lookup scratch, GPU and RSS. No full-scene fractional motion or live handoff integration.')
(out/'writer-native-scene-test-report.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in ['rows','diagnostic_images']})
