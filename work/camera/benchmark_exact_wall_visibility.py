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
from unittest.mock import patch
import owned_closed_scene_memory as memory
import owned_sampled_graph_gpu as visibility
from owned_wall_visibility_candidate import helper as native_resource_helper
corrections=visibility.selected_graph_walls
native_resource_helper()
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-visibility-native-integration-20261006/visibility-before.py').read_text(),prior)
resource_before=native_resource_helper.cache_info()
times={'before':[],'after':[]};cpu={'before':[],'after':[]};cold_caches=set()
for module_name,module in list(sys.modules.items()):
 if module_name.startswith('owned_') or module_name=='sample_owned_motion':
  for value in vars(module).values():
   if callable(getattr(value,'cache_clear',None)) and value is not native_resource_helper:cold_caches.add(value)
for repeat in range(10):
 order=[('before',prior['selected_graph_walls']),('after',corrections)]
 if repeat%2:order.reverse()
 for name,cls in order:
  for cache in cold_caches:cache.cache_clear()
  memory._scene_memory_local.entries=[]
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
  try:
   with patch.object(visibility,'selected_graph_walls',cls):
    start=time.perf_counter_ns();cpu_start=time.thread_time_ns()
    prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=[prepared.sample(x['alpha']) for x in expected]
    end=time.perf_counter_ns();cpu_end=time.thread_time_ns()
    actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
    times[name].append((end-start)/1e6);cpu[name].append((cpu_end-cpu_start)/1e6)
  finally:
   if prepared is not None:prepared.close()
   history.close()
resource_after=native_resource_helper.cache_info()
assert resource_after.misses==resource_before.misses and resource_after.currsize==1
result=dict(native_resource_loads_during_trials=resource_after.misses-resource_before.misses,result='PASS_ALL_LIVE_SIGNATURES',trials=20,cold_global_cache_count=len(cold_caches),wall_median_ms={k:statistics.median(v) for k,v in times.items()},wall_range_ms={k:[min(v),max(v)] for k,v in times.items()},coarse_cpu_median_ms={k:statistics.median(v) for k,v in cpu.items()},scope='Exact captured native history/roads; old Python vs integrated native wall visibility; cold transform caches; warm imports and native resource loader; excludes live timing')
Path('work/camera/exact-live-state-wall-visibility-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
