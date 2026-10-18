"""Read-only owner-key geometry stability probe; not a cache implementation or FPS test."""
from pathlib import Path
from collections import OrderedDict
import argparse,ctypes as C,hashlib,json,os,struct
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-owner-identity-tests';out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--frames',type=int,default=1200);options=parser.parse_args();assert options.frames==1200
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();core_dir=base/'NFSUG-pc-source-transfer-core';reader_dir=base/'NFSUG-pc-source-reader-direct-tests'
cr=json.loads((core_dir/'source-transfer-core-test-report.json').read_text());rr=json.loads((reader_dir/'reader-direct-test-report.json').read_text());assert cr['result']=='PASS_SOURCE_TRANSFER_CORE_PARITY' and rr['result']=='PASS_MAINTAINED_SOURCE_READER_DIRECT'
for report in (cr,rr):
 for n,h in report['source_sha256'].items():assert sha(source/n)==h,n
assert cr['core_sha256']==sha(core_dir/'capture-host.dll') and rr['dll_sha256']==sha(reader_dir/'source-reader.dll')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(core_dir/'capture-host.dll'));reader=C.CDLL(str(reader_dir/'source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,result=I):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);timing=fn(core,'nfa_core_timing',[P,P]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S)
bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);free=fn(reader,'nf_pc_source_frame_free',[P],None);meta=fn(reader,'nf_pc_source_frame_info',[P,P]);owner=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,C.POINTER(P),C.POINTER(S)])
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state_path=root/'work/integration-0.state';state=state_path.read_bytes();before={str(p):sha(p) for p in [rom,state_path]};h=op(os.fsencode(rom));assert h and load(h,state,len(state))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api))
r=rop(C.byref(api),64*1024*1024,C.cast(core.nfa_core_capture_background_take,P),C.cast(core.nfa_core_capture_owned_free,P),C.cast(core.nfa_core_capture_source_world_take,P),C.cast(core.nfa_core_capture_source_world_free,P));assert r
cache=OrderedDict();history={};cached_bytes=peak=seen=repeats=exact_repeats=equal_bytes=frames=missing=steps=samples=0;failures=[];pcm=(C.c_int16*8192)();audio_hash=hashlib.sha256();baseline=(Q*4)();assert timing(h,baseline)
def body(f,index):
 global cached_bytes,peak,seen,repeats,exact_repeats,equal_bytes
 m=(Q*8)();assert meta(f,m)
 for i in range(m[4]):
  key=(Q*5)();assert owner(f,i,key);identity=tuple(key);p=P();n=S();assert component(f,i,1,C.byref(p),C.byref(n));data=C.string_at(p,n.value);digest=hashlib.sha256(data).hexdigest();seen+=1
  if identity in history:
   repeats+=1;old_size,old_hash,old_step=history[identity]
   if old_size!=len(data) or old_hash!=digest or (identity in cache and cache[identity]!=data):
    difference=dict(step=index+1,owner=i,key=list(identity),first_step=old_step,old_size=old_size,new_size=len(data),old_sha256=old_hash,new_sha256=digest)
    if identity in cache:
     previous=cache[identity];difference['first_difference']=next((j for j,(a,b) in enumerate(zip(previous,data)) if a!=b),min(len(previous),len(data)));(out/'before.nsp').write_bytes(previous);(out/'after.nsp').write_bytes(data)
    failures.append(difference);return False
   if identity in cache:exact_repeats+=1;equal_bytes+=len(data)
  else:history[identity]=(len(data),digest,index+1)
  if identity in cache:cached_bytes-=len(cache.pop(identity))
  while cache and (len(cache)>=4 or cached_bytes+len(data)>64*1024*1024):cached_bytes-=len(cache.popitem(last=False)[1])
  if len(data)<=64*1024*1024:cache[identity]=data;cached_bytes+=len(data);peak=max(peak,cached_bytes)
 return True
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(options.frames):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;steps+=1
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==baseline[2]+steps and tick[3]==steps
   if index<600:assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;audio_hash.update(C.string_at(pcm,n*4))
   f=capture(r,64*1024*1024)
   if not f:missing+=1;continue
   try:frames+=1;ok=body(f,index)
   finally:free(f)
   if not ok:break
 if not failures:
  assert steps==1200 and frames==1190 and missing==10 and audio_hash.hexdigest()=='84d8e27f4ecdf97eff82a279523a546331d31c7c03b2b6f5723462d485ec08be'
  old_epochs={key[0] for key in history};assert load(h,state,len(state)) and not capture(r,64*1024*1024)
  reset_epochs=set()
  for i in range(80):
   assert step(h,1|(16 if 60<=i<120 else 0))==1
   while audio(h,pcm,4096):pass
   f=capture(r,64*1024*1024)
   if f:
    m=(Q*8)();assert meta(f,m);reset_epochs.add(m[0]);free(f)
  assert reset_epochs and old_epochs.isdisjoint(reset_epochs)
  assert fn(core,'nfa_core_capture_enable',[P,I])(h,0) and not capture(r,64*1024*1024)
finally:rclose(r);close(h)
for name in ['background','geometry']:
 counts=(Q*3)();assert fn(core,'nfa_core_capture_owned_'+name+'_info',[P])(counts) and counts[0]==counts[1]
assert before=={str(p):sha(p) for p in [rom,state_path]}
report=dict(result='OWNER_GEOMETRY_IDENTITY_CHANGED' if failures else 'PASS_OBSERVED_OWNER_GEOMETRY_IDENTITY_STABLE',steps=steps,complete_frames=frames,startup_capture_failures=missing,owner_requests=seen,distinct_owner_keys=len(history),repeat_keys=repeats,exact_byte_repeat_comparisons=exact_repeats,exact_repeat_bytes=equal_bytes,maximum_comparison_cache_bytes=peak,comparison_cache_limit_bytes=64*1024*1024,failures=failures,first_600_original_pixels_exact=True,audio_frames=samples,audio_sha256=audio_hash.hexdigest(),reset_epoch_separation_verified=not failures,transfers_balanced_after_core_close=True,rom_state_unchanged=True,cache_implementation_added=False,full_scene_60fps=False,scope='Observed this scripted segment only; not a universal producer immutability proof.',source_sha256={n:sha(source/n) for n in ['source_frame.c','source_frame.h','source_reader.c','source_reader.h','source_transfer_observer.inc','source_transfer_core_api.inc']},core_sha256=sha(core_dir/'capture-host.dll'),reader_sha256=sha(reader_dir/'source-reader.dll'),probe_sha256=sha(Path(__file__)))
(out/'owner-identity-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
