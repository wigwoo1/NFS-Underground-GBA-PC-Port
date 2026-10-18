import gc,json,weakref
from collections import Counter
from pathlib import Path
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(source,'captured-lifetime-setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
previous_enabled=gc.isenabled();previous_debug=gc.get_debug();gc.collect();previous_garbage=len(gc.garbage);refs=[];counts=[]
try:
 gc.disable()
 for iteration in range(12):
  local_history=EndpointRoadPlanner(rom,table);local_history.scratch=restore(local_history.d,h['scratch']);local_history.epoch=h['epoch'];local_history.refresh=h['refresh']
  local_prepared=PreparedWorldMotion(*frames,*scenes,local_history,roads,rom);refs.append(weakref.ref(local_prepared))
  cached=PrecomputedSourceWorldSamples(local_prepared,alphas)
  values=[signature(cached.sample(a)) for a in alphas]
  if iteration==0:expected=values
  else:assert values==expected
  cached.close();local_prepared.close();local_history.close();del cached,local_prepared,local_history,values
  counts.append(sum(x() is not None for x in refs))
 gc.set_debug(gc.DEBUG_SAVEALL);collected=gc.collect();new=gc.garbage[previous_garbage:];types=Counter(type(x).__module__+'.'+type(x).__qualname__ for x in new)
 out=dict(result='PASS_BOUNDED_CAPTURED_OWNER_LIFETIME',rounds=12,retired_prepared_alive=counts,unreachable_collected=collected,unreachable_saved=len(new),types=dict(types),scope='Isolated captured preparation fixture only. Automatic GC temporarily disabled for bounded inventory, restored afterward; never live policy. DEBUG_SAVEALL identifies unreachable objects, not which trigger scan time.')
 assert not any(counts)
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010');(cp/'captured-owner-lifetime.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:
 gc.set_debug(previous_debug);del gc.garbage[previous_garbage:]
 if previous_enabled:gc.enable()
 else:gc.disable()
 gc.collect()
