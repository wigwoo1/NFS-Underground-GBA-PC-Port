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
import owned_sampled_world_frame as assembly
from owned_sampled_road_sequence import SampledRoadSequence
from owned_wall_visibility_candidate import helper as native_resource_helper
from sample_owned_motion import PreparedMotionPair,rigid_library
native_resource_helper();rigid_library();rows=[]
for trial in range(11):
 caches=set()
 for name,module in list(sys.modules.items()):
  if name.startswith('owned_') or name=='sample_owned_motion':
   for value in vars(module).values():
    if callable(getattr(value,'cache_clear',None)) and value is not native_resource_helper and value is not rigid_library:caches.add(value)
 for cache in caches:cache.cache_clear()
 memory._scene_memory_local.entries=[]
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;stages={};samples=[];sample_ms=[]
 def measure(name,fn):
  def wrapped(*args,**kwargs):
   begin=time.perf_counter_ns()
   try:return fn(*args,**kwargs)
   finally:stages[name]=stages.get(name,0)+time.perf_counter_ns()-begin
  return wrapped
 try:
  begin=time.perf_counter_ns();prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);construct_ms=(time.perf_counter_ns()-begin)/1e6
  replacements={n:measure(n,getattr(assembly,n)) for n in ('sampled_graph_gpu_records','sampled_gpu_records','model_record_owners','sampled_model_visit','encode')}
  with patch.multiple(assembly,**replacements),patch.object(SampledRoadSequence,'sample',measure('road_sequence',SampledRoadSequence.sample)),patch.object(PreparedMotionPair,'sample',measure('motion_sample_inclusive',PreparedMotionPair.sample)):
   for x in expected:
    begin=time.perf_counter_ns();samples.append(prepared.sample(x['alpha']));sample_ms.append((time.perf_counter_ns()-begin)/1e6)
  actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
  rows.append(dict(trial=trial,construct_ms=construct_ms,sample_ms=sample_ms,stage_ms={k:v/1e6 for k,v in stages.items()}))
 finally:
  if prepared is not None:prepared.close()
  history.close()
warm=rows[1:];keys={k for row in warm for k in row['stage_ms']}
result=dict(result='PASS_ALL_COMPLETE_SIGNATURES',samples=len(expected)*len(rows),construct_median_ms=statistics.median(x['construct_ms'] for x in warm),all_samples_median_ms=statistics.median(sum(x['sample_ms']) for x in warm),stage_median_ms={k:statistics.median(x['stage_ms'].get(k,0) for x in warm) for k in sorted(keys)},trials=rows,scope='Actual captured scene/history/roads; cold transform caches, warm imports; lightweight wrappers timed inclusive stages, excludes GPU/live cadence')
Path('work/camera/captured-unprofiled-stage-timing.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='trials'})
