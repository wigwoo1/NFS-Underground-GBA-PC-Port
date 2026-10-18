import runpy,time,statistics
from pathlib import Path
import owned_sampled_graph_wall_visibility as selection
from owned_continuous_wall_visibility import sampled_edge,_ring_endpoint_corrections
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');portal=v['prepared'].pair.portal
before={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-endpoint-correction-cache-20261006/before.py').read_text(),before)
try:
 for i in range(101):
  selection.sampled_edge=before['sampled_edge'];a=selection.selected_graph_walls(portal,i/100)
  selection.sampled_edge=sampled_edge;b=selection.selected_graph_walls(portal,i/100)
  assert a==b,i
 timing=[[],[]]
 for repeat in range(6):
  for index in ((0,1) if repeat%2==0 else (1,0)):
   selection.sampled_edge=(before['sampled_edge'],sampled_edge)[index];begin=time.perf_counter_ns()
   for i in range(1,100):selection.selected_graph_walls(portal,i/100)
   timing[index].append((time.perf_counter_ns()-begin)/1e6)
 assert _ring_endpoint_corrections.cache_info().currsize<=32
 print('PASS101 exact wall visibility/material/clip outputs; bounded corrections; median99sample ms',*[statistics.median(x) for x in timing])
finally:selection.sampled_edge=sampled_edge
