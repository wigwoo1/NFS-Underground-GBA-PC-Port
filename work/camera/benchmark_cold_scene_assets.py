"""Cold complete-scene asset construction, per-stage elapsed and thread CPU."""
import sys,time,json,statistics
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
setup=Path('work/camera/profile_sequential_world_preparation.py').read_text().split('def prepare():')[0]
exec(compile(setup,'fixture_setup','exec'))
rows=[];expected={};checks=0
try:
 for repeat in range(5):
  for index,(_,scene) in enumerate(pairs):
   a=time.perf_counter_ns();ca=time.thread_time_ns();memory=ClosedSceneMemory(scene.graph,rom);b=time.perf_counter_ns();cb=time.thread_time_ns();sources=road_candidates(scene.graph,memory);c=time.perf_counter_ns();cc=time.thread_time_ns()
   value=(memory._ranges,tuple(sources))
   if index in expected:assert value==expected[index];checks+=1
   else:expected[index]=value
   rows.append(dict(index=index,refresh=scene.graph.refresh,memory_wall_ns=b-a,memory_cpu_ns=cb-ca,candidates_wall_ns=c-b,candidates_cpu_ns=cc-cb,ranges=len(memory._ranges),owned_bytes=memory.owned_byte_count,roads=len(sources)))
finally:history.close()
keys=['memory_wall_ns','memory_cpu_ns','candidates_wall_ns','candidates_cpu_ns']
out=dict(result='PASS',exact_rebuild_checks=checks,scene_count=len(pairs),stages={k:dict(total_ms=sum(x[k] for x in rows)/1e6,median_ms=statistics.median(x[k] for x in rows)/1e6,max_ms=max(x[k] for x in rows)/1e6) for k in keys},rows=rows,scope='Cold exact scene asset component, no GPU/game-clock/full-route verification; Windows thread CPU coarse')
p=Path(sys.argv[1]).with_suffix('.cold-scene-assets.json');p.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
