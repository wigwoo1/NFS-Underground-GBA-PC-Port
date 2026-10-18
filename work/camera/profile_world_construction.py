"""Isolated complete pair construction, history advance and first sampling."""
import runpy,cProfile,pstats,time,json
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
import sys,struct
if Path(sys.argv[1]).suffix=='.json':
 from owned_closed_graph import ClosedGraph
 from owned_closed_supplements import ClosedSupplements
 from owned_model_builder_inputs import OwnedModelBuilders
 from owned_model_sources import OwnedModelSources
 from owned_motion_scene import MotionScene
 r=json.loads(Path(sys.argv[1]).read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();scenes=[];frames=[]
 pair_index=int(sys.argv[sys.argv.index('--pair-index')+1]) if '--pair-index' in sys.argv else 0
 selected=r['model_scene_captures'][pair_index:pair_index+2]
 if len(selected)!=2:raise ValueError('Incomplete selected capture pair')
 for c in selected:
  closed=ClosedGraph.decode(Path(c['graph']).read_bytes());scenes.append(MotionScene(closed,ClosedSupplements.decode(Path(c['supplements']).read_bytes(),closed,rom),OwnedModelBuilders(Path(c['builders']).read_bytes()),OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),closed)));frames.append(Path(c['frame']).read_bytes())
 v=dict(rom=rom,scenes=scenes,data=dict(frames=frames,table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])))
else:v=runpy.run_path('work/camera/audit_failed_world_motion.py')
data=v['data'];history=EndpointRoadPlanner(v['rom'],data['table']);roads,_=history.plan(v['scenes'][0].graph)
def construct():
 for i in range(10):
  p=PreparedWorldMotion(*data['frames'],*v['scenes'],history,roads,v['rom'])
  try:
   if "--samples" in sys.argv:
    for alpha in (.25,.5,.75):p.sample(alpha)
   else:p.sample(.5)
  finally:p.close()
try:
 profile=cProfile.Profile();start=time.perf_counter_ns();profile.runcall(construct);elapsed=time.perf_counter_ns()-start
 path=Path('work/camera/prototype-runs/world-construction-'+str(time.time_ns())+'.prof');profile.dump_stats(str(path))
 with path.with_suffix('.txt').open('w') as f:pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(35)
 path.with_suffix('.json').write_text(json.dumps(dict(iterations=10,elapsed_ms=elapsed/1e6,scope='Single thread pair construction plus three samples' if '--samples' in sys.argv else 'Single thread pair construction plus first sample; profiling overhead, not live timing proof'),indent=2))
 print(path);print(path.with_suffix('.txt').read_text())
finally:history.close()
