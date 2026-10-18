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
rows=[]
for trial in range(20):
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
 stop.clear();thread=None
 if trial%2:
  thread=threading.Thread(target=run_producer);thread.start()
 try:
  begin=time.perf_counter_ns();cpu_begin=time.thread_time_ns()
  prepared=profile.run(PreparedWorldMotion,*frames,*scenes,history,roads,rom) if profile else PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  samples=[profile.run(prepared.sample,x['alpha']) if profile else prepared.sample(x['alpha']) for x in expected]
  end=time.perf_counter_ns();cpu_end=time.thread_time_ns()
  actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
  rows.append(dict(concurrent_producer=bool(trial%2),trial=trial,profiled=profile is not None,wall_ms=(end-begin)/1e6,coarse_cpu_ms=(cpu_end-cpu_begin)/1e6,cleared_transform_caches=len(caches)))
  if profile:profile.save(Path('work/camera/captured-preparation-'+('initial' if trial==0 else 'warm')+'-cpu-profile.json'))
 finally:
  if prepared is not None:prepared.close()
  history.close()
  if thread is not None:stop.set();thread.join(10);assert not thread.is_alive()
producer.nf_close();assert not producer_errors,producer_errors
result=dict(result='PASS_ALL_COMPLETE_SIGNATURES',samples_per_trial=len(expected),trials=rows,warm_unprofiled_median_ms=statistics.median(x['wall_ms'] for x in rows if not x['profiled']),original_producer_updates=producer_updates,baseline_median_ms=statistics.median(x['wall_ms'] for x in rows if not x['concurrent_producer']),concurrent_median_ms=statistics.median(x['wall_ms'] for x in rows if x['concurrent_producer']),scope='Alternating identical captured preparation with/without a paced original-cycle producer. No live scene capture or GPU presentation; not full60fps or exclusive scheduling cause proof')
Path('work/camera/captured-preparation-concurrent-comparison.json').write_text(json.dumps(result,indent=2));print(result)
