"""Single-thread consecutive source history profile without repeating one pair."""
import json,struct,sys,cProfile,pstats,time
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
r=json.loads(Path(sys.argv[1]).read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();pairs=[]
for c in r['model_scene_captures']:
 g=ClosedGraph.decode(Path(c['graph']).read_bytes());pairs.append((Path(c['frame']).read_bytes(),MotionScene(g,ClosedSupplements.decode(Path(c['supplements']).read_bytes(),g,rom),OwnedModelBuilders(Path(c['builders']).read_bytes()),OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),g))))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(pairs[0][1].graph);count=0

def prepare():
 global history,roads,count
 for older,newer in zip(pairs,pairs[1:]):
  p=PreparedWorldMotion(older[0],newer[0],older[1],newer[1],history,roads,rom)
  try:
   advanced=p.take_next_history();history.close();history=advanced;roads=p.endpoint_roads[1]
   for alpha in (.25,.5,.75):p.sample(alpha);count+=1
  finally:p.close()
try:
 profile=cProfile.Profile();start=time.perf_counter_ns();profile.runcall(prepare);elapsed=time.perf_counter_ns()-start
 path=Path('work/camera/prototype-runs/sequential-world-'+str(time.time_ns())+'.prof');profile.dump_stats(str(path))
 with path.with_suffix('.txt').open('w') as f:pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(25)
 path.with_suffix('.json').write_text(json.dumps(dict(samples=count,intervals=len(pairs)-1,elapsed_ms=elapsed/1e6,scope='single-thread consecutive captured history, includes profiler overhead; not live clock'),indent=2));print(path);print(path.with_suffix('.txt').read_text())
finally:history.close()
