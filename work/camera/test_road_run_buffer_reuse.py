import json,struct,time,statistics,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_endpoint_road_planner import EndpointRoadPlanner
scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-run-buffer-reuse-20261006/before.py').read_text(),'before.py','exec'),scope);Old=scope['EndpointRoadPlanner']
r=json.loads(Path(sys.argv[1]).read_text());scenes=[ClosedGraph.decode(Path(c['graph']).read_bytes()) for c in r['model_scene_captures']]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);timings=[[],[]];checks=0
for iteration in range(12):
 planners=[Old(rom,table),EndpointRoadPlanner(rom,table)]
 try:
  for c in scenes:
   results=[None,None]
   for index in ((0,1) if iteration%2==0 else (1,0)):
    start=time.perf_counter_ns();results[index]=planners[index].plan(c);timings[index].append(time.perf_counter_ns()-start)
   assert results[0]==results[1];checks+=1
  parent=planners[1];child=parent.fork()
  try:
   assert not hasattr(child,'_run_output')
   assert parent._run_output is not None
  finally:child.close()
 finally:
  for p in planners:p.close()
result=dict(exact_endpoint_plans=checks,private_fork_buffer=True,reference_total_ms=sum(timings[0])/1e6,candidate_total_ms=sum(timings[1])/1e6,reference_median_ms=statistics.median(timings[0])/1e6,candidate_median_ms=statistics.median(timings[1])/1e6,scope='complete sequential endpoint road plans; live timing unverified')
Path('work/camera/prototype-runs/road-run-buffer-reuse.json').write_text(json.dumps(result,indent=2));print(result)
