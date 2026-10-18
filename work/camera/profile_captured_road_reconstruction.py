import sys,json,time,statistics
from pathlib import Path
source=Path('work/camera/profile_captured_preparation_warm.py').read_text().split('import statistics')[0]
exec(compile(source,'captured-setup','exec'))
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_thread_profile import ThreadProfile
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('outputs/nfsug-native-renderer/camera-research/checkpoints/captured-road-reconstruction-20261006');out.mkdir(exist_ok=True)
rows=[]
for index,scene in enumerate(scenes):
 closed=scene.graph;reference=None
 for trial in range(8):
  profiler=ThreadProfile() if trial==7 else None
  start=time.perf_counter_ns()
  mem=profiler.run(ClosedSceneMemory,closed,rom) if profiler else ClosedSceneMemory(closed,rom)
  middle=time.perf_counter_ns()
  candidates=profiler.run(road_candidates,closed,mem) if profiler else road_candidates(closed,mem)
  end=time.perf_counter_ns()
  exact=([vars(x) for x in candidates],mem._ranges,mem.missing)
  if reference is None:reference=exact
  else:assert exact==reference
  rows.append(dict(endpoint=index,refresh=closed.refresh,trial=trial,profiled=profiler is not None,memory_ms=(middle-start)/1e6,candidates_ms=(end-middle)/1e6,count=len(candidates),owned_ranges=len(mem._ranges),owned_bytes=mem.owned_byte_count))
  if profiler:profiler.save(out/('endpoint-'+str(index)+'-profile.json'))
(out/'tests.json').write_text(json.dumps(dict(result='PASS_EXACT_RECONSTRUCTION',capture=str(folder),trials=rows,scope='Two immutable captured complete scene endpoints, repeated memory/candidate parity; profiles separate from unprofiled timings; not fullscene60fps proof'),indent=2))
print('PASS',[(i,statistics.median(x['memory_ms'] for x in rows if x['endpoint']==i and not x['profiled']),statistics.median(x['candidates_ms'] for x in rows if x['endpoint']==i and not x['profiled'])) for i in range(2)])
