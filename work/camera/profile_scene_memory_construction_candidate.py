import sys,json,time,statistics
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(source,'saved_scene_memory_fixture','exec'))
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_pointer_decode_candidate import ClosedSceneMemory as Candidate
from owned_complete_road_candidates import road_candidates
import cProfile,pstats,io
try:
 profiler=cProfile.Profile();profiler.enable()
 for i in range(100):
  for scene in scenes:Baseline(scene.graph,rom)
 profiler.disable();stream=io.StringIO();pstats.Stats(profiler,stream=stream).strip_dirs().sort_stats('cumtime').print_stats(18)
 Path('work/camera/prototype-runs/scene-memory-construction-profile.txt').write_text(stream.getvalue());print(stream.getvalue())
finally:history.close()
