"""Whole complete-scene sampling benchmark against pre-height-cache wall code."""
import sys,json,time,statistics
from pathlib import Path
import owned_motion_visibility as visibility
from test_scene_process_transport import digest
setup=Path('work/camera/profile_sequential_world_preparation.py').read_text().split('def prepare():')[0]
exec(compile(setup,'fixture_setup','exec'))
reference={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/portal-sample-bounded-reuse-20261006/before-visibility.py').read_text(),'reference','exec'),reference)
candidate=visibility.PortalMotionPair.sample;timings=[[],[]];checks=0
try:
 for older,newer in zip(pairs,pairs[1:]):
  prepared=PreparedWorldMotion(older[0],newer[0],older[1],newer[1],history,roads,rom)
  advanced=prepared.take_next_history();history.close();history=advanced;roads=prepared.endpoint_roads[1]
  try:
   expected={}
   for repeat in range(4):
    for mode in (repeat%2,1-repeat%2):
     fn=reference['PortalMotionPair'].sample if mode==0 else candidate;visibility.PortalMotionPair.sample=fn
     prepared.pair.portal._sample_cache.clear();prepared.pair.portal._sample_alpha=None
     t=time.perf_counter_ns();samples=[prepared.sample(a) for a in (.25,.5,.75)];timings[mode].append((time.perf_counter_ns()-t)/1e6)
     for alpha,sample in zip((.25,.5,.75),samples):
      value=digest(sample)
      if alpha in expected:assert value==expected[alpha];checks+=1
      else:expected[alpha]=value
  finally:prepared.close()
finally:visibility.PortalMotionPair.sample=candidate;history.close()
result=dict(exact_repeated_samples=checks,reference_total_ms=sum(timings[0]),candidate_total_ms=sum(timings[1]),reference_median_ms=statistics.median(timings[0]),candidate_median_ms=statistics.median(timings[1]),scope='whole complete-scene sampled intervals; repeated prepared pairs, no live scheduling or cold constructors')
output=Path(sys.argv[1]).with_suffix('.portal-sample-world-benchmark.json');output.write_text(json.dumps(result,indent=2));print(result)
