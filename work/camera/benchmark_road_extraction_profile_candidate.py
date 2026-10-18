import sys,json,struct,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'savedscene','exec'))
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
import cProfile,pstats,io,time,statistics
try:
 memories=[ClosedSceneMemory(scene.graph,rom) for scene in scenes]
 samples=[]
 profiler=cProfile.Profile()
 for iteration in range(120):
  begin=time.perf_counter_ns()
  for scene,memory in zip(scenes,memories):road_candidates(scene.graph,memory)
  samples.append((time.perf_counter_ns()-begin)/2e6)
 profiler.enable()
 for iteration in range(120):
  for scene,memory in zip(scenes,memories):road_candidates(scene.graph,memory)
 profiler.disable()
 stream=io.StringIO();pstats.Stats(profiler,stream=stream).strip_dirs().sort_stats('cumtime').print_stats(18)
 out=dict(result='ROAD_EXTRACTION_PROFILE_COMPLETE',median_ms=statistics.median(samples),samples_ms=samples,profile=stream.getvalue(),scope='Two saved scenes, 120 unprofiled paired iterations followed by separate profiled iterations; no live cadence claim.')
 Path('work/camera/prototype-runs/road-extraction-profile-20261009.json').write_text(json.dumps(out,indent=2))
 print(out['median_ms']);print(out['profile'])
finally:history.close()

