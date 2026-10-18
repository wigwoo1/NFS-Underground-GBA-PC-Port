import sys,json,time
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import statistics
import owned_closed_scene_memory as memory
from owned_wall_visibility_candidate import helper as native_resource_helper
from owned_thread_profile import ThreadProfile
native_resource_helper()
import ctypes as C,threading
running=threading.Event();active=threading.Event();idle=threading.Event();terminate=threading.Event();gpu_ready=threading.Event();gpu_errors=[];gpu_rows=[]
def run_gpu():
 env={}
 try:
  setup=Path('work/camera/test_sky_concurrent_producer.py').read_text().split('import time,statistics')[0]
  exec(compile(setup,'fixed-gpu-setup','exec'),env)
  d=env['d'];api=env['api'];frame=env['frame'];arrays=env['arrays'];samples=env['samples'];count=env['count'];epoch=env['h'][6]
  d.nf_owned_gpu_present.argtypes=[C.c_uint64]
  assert d.nf_owned_gpu_window(1)==0
  reference=env['draw'](frame);gpu_ready.set()
  while not terminate.is_set():
   idle.set()
   if not active.wait(.01):continue
   idle.clear();running.set();origin=time.perf_counter_ns();index=0
   while active.is_set() and not terminate.is_set():
    began=time.perf_counter_ns()
    assert api(frame,len(frame),arrays['camera'],arrays['models'],arrays['bounds'],count,samples.lower,samples.upper,15136,samples.weight)==0
    assert d.nf_owned_gpu_present(epoch)==0
    gpu_rows.append(dict(draw_present_ns=time.perf_counter_ns()-began));index+=1
    remaining=(origin+int(index*1e9/60)-time.perf_counter_ns())/1e9
    if remaining>0:terminate.wait(remaining)
  assert env['draw'](frame)==reference
 except BaseException as e:gpu_errors.append(str(e));gpu_ready.set()
 finally:
  if 'd' in env:assert env['d'].nf_owned_gpu_close()
  idle.set()
producer=C.CDLL(str(Path('work/nfsprobe.dll').resolve()))
producer.nf_init.argtypes=[C.c_char_p,C.c_char_p];producer.nf_state.argtypes=[C.c_char_p,C.c_int]
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
assert producer.nf_init(str(rom_path).encode(),b'') and producer.nf_state(str(Path('work/race.state').resolve()).encode(),0)
stop=threading.Event();producer_updates=[];producer_errors=[]
def run_producer():
 try:
  origin=time.perf_counter_ns();index=0
  while not stop.is_set():
   remaining=(origin+int(index*280896*1e9/16777216)-time.perf_counter_ns())/1e9
   if remaining>0 and stop.wait(remaining):break
   producer.nf_frame(1);index+=1
  producer_updates.append(index)
 except BaseException as e:producer_errors.append(str(e))

gpu_thread=threading.Thread(target=run_gpu);gpu_thread.start();assert gpu_ready.wait(30) and not gpu_errors,gpu_errors
try:
 rows=[]
 for trial in range(40):
  # Discover transform caches after each pass: first-use imports can add caches.
  caches=set()
  for name,module in list(sys.modules.items()):
   if name.startswith('owned_') or name=='sample_owned_motion':
    for value in vars(module).values():
     if callable(getattr(value,'cache_clear',None)) and value is not native_resource_helper:caches.add(value)
  for cache in caches:cache.cache_clear()
  memory._scene_memory_local.entries=[]
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
  profile=None
  active.clear();assert idle.wait(10)
  producer_thread=None;stop.clear()
  if trial%2:
   producer_thread=threading.Thread(target=run_producer);producer_thread.start()
   running.clear();active.set();assert running.wait(10)
  try:
   begin=time.perf_counter_ns();cpu_begin=time.thread_time_ns()
   prepared=profile.run(PreparedWorldMotion,*frames,*scenes,history,roads,rom) if profile else PreparedWorldMotion(*frames,*scenes,history,roads,rom)
   samples=[profile.run(prepared.sample,x['alpha']) if profile else prepared.sample(x['alpha']) for x in expected]
   end=time.perf_counter_ns();cpu_end=time.thread_time_ns()
   actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
   rows.append(dict(concurrent_gpu=bool(trial%2),trial=trial,profiled=profile is not None,wall_ms=(end-begin)/1e6,coarse_cpu_ms=(cpu_end-cpu_begin)/1e6,cleared_transform_caches=len(caches)))
   if profile:profile.save(Path('work/camera/captured-preparation-'+('initial' if trial==0 else 'warm')+'-cpu-profile.json'))
  finally:
   if prepared is not None:prepared.close()
   history.close()
   active.clear();assert idle.wait(10)
   if producer_thread is not None:
    stop.set();producer_thread.join(10);assert not producer_thread.is_alive()
finally:
 stop.set()
 if producer_thread is not None and producer_thread.is_alive():producer_thread.join(10)
 producer.nf_close();assert not producer_errors,producer_errors
 terminate.set();active.set();gpu_thread.join(10);assert not gpu_thread.is_alive() and not gpu_errors,gpu_errors
result=dict(original_producer_updates=producer_updates,result='PASS_ALL_COMPLETE_SIGNATURES',samples_per_trial=len(expected),trials=rows,warm_unprofiled_median_ms=statistics.median(x['wall_ms'] for x in rows if not x['profiled']),gpu_presentations=len(gpu_rows),gpu_max_draw_present_ms=max(x["draw_present_ns"] for x in gpu_rows)/1e6,baseline_median_ms=statistics.median(x['wall_ms'] for x in rows if not x['concurrent_gpu']),concurrent_median_ms=statistics.median(x['wall_ms'] for x in rows if x['concurrent_gpu']),scope='Alternating identical captured preparation with/without fixed fullscene4K presentation on another thread. Simultaneous paced original game producer plus fixed4K GPU during concurrent trials; no live scene capture; repeated scene pixels exact; not full60fps or exclusive scheduling cause proof')
Path('work/camera/captured-preparation-combined-comparison.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='trials'})
