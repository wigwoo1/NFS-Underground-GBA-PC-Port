import runpy,time,statistics
from pathlib import Path
from owned_endpoint_road_selection import endpoint_road_span_candidates
from owned_closed_scene_memory import scene_memory
from owned_complete_road_candidates import road_candidates
v=runpy.run_path('work/camera/profile_world_construction.py');namespace=dict(__file__=str(Path('work/camera/owned_endpoint_road_selection.py').resolve()));exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-point-native-copy-20261006/before.py').read_text(),namespace);before=namespace['endpoint_road_span_candidates'];a=[];b=[]
for iteration in range(10):
 for closed in (s.graph for s in v['v']['scenes']):
  memory=scene_memory(closed,v['v']['rom']);sources=road_candidates(closed,memory)
  functions=(before,endpoint_road_span_candidates) if iteration%2==0 else (endpoint_road_span_candidates,before);results={}
  for fn in functions:
   start=time.perf_counter_ns();results[fn]=fn(closed,memory,sources,v['data']['table'],include_empty=True);(a if fn is before else b).append(time.perf_counter_ns()-start)
  assert results[before]==results[endpoint_road_span_candidates]
print('PASS40 endpoint road selections exact record/order/span parity; medianms',round(statistics.median(a)/1e6,3),round(statistics.median(b)/1e6,3))
