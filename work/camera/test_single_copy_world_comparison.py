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
rows=[]
import runpy
import owned_prepared_world_motion as target
optimized=target.assemble_world
reference=runpy.run_path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-single-copy-world-20261006/before.py')['assemble_world']
for trial in range(6):
 target.assemble_world=reference if trial%2==0 else optimized
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
 try:
  begin=time.perf_counter_ns();cpu_begin=time.thread_time_ns()
  prepared=profile.run(PreparedWorldMotion,*frames,*scenes,history,roads,rom) if profile else PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  samples=[profile.run(prepared.sample,x['alpha']) if profile else prepared.sample(x['alpha']) for x in expected]
  end=time.perf_counter_ns();cpu_end=time.thread_time_ns()
  actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
  rows.append(dict(variant='before' if trial%2==0 else 'after',trial=trial,profiled=profile is not None,wall_ms=(end-begin)/1e6,coarse_cpu_ms=(cpu_end-cpu_begin)/1e6,cleared_transform_caches=len(caches)))
  if profile:profile.save(Path('work/camera/captured-preparation-'+('initial' if trial==0 else 'warm')+'-cpu-profile.json'))
 finally:
  if prepared is not None:prepared.close()
  history.close()
result=dict(result='PASS_ALL_COMPLETE_SIGNATURES',samples_per_trial=len(expected),trials=rows,warm_unprofiled_median_ms=statistics.median(x['wall_ms'] for x in rows if not x['profiled']),scope='Same immutable captured history/roads; cold discovered transform caches each trial, warm native resource; initial/warm profile overhead excluded from unprofiled median; no live cadence proof')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-single-copy-world-20261006/alternating-comparison.json').write_text(json.dumps(result,indent=2));print(result)
