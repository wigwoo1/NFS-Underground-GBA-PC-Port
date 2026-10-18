from pathlib import Path
import time,json,statistics,struct
from owned_graph_packet import GraphPacket
from owned_wall_projection import projected
from owned_wall_projection_eager_reference import projected as eager
p=Path('work/camera');raw=(p/'road-correction-reciprocal.bin').read_bytes();reciprocal=struct.unpack('<32768I',raw[:131072]);checks=[]
for file in sorted((p/'graph-packets').glob('*.ngp')):
 g=GraphPacket.decode(file.read_bytes());expected=eager(g,reciprocal);actual=projected(g,reciprocal);assert actual==expected
 costs=[[],[]]
 for i in range(8):
  for index,fn in ((0,eager),(1,projected)) if i%2==0 else ((1,projected),(0,eager)):
   start=time.perf_counter_ns();result=fn(g,reciprocal);costs[index].append((time.perf_counter_ns()-start)/1e6);assert result==expected
 before,after=map(statistics.median,costs);checks.append(dict(refresh=g.refresh,exact_draws=len(actual[0]),eager_median_ms=before,selected_median_ms=after,speedup=before/after))
r=dict(result='PASS_SELECTED_REGION_WALL_TRANSFORM_PARITY_COST',checks=checks,scope='Same-input alternating component benchmark, exact scratch/selection/stat parity; not full-scene timing or60fps gameplay.')
(p/'owned-wall-transform-cost.json').write_text(json.dumps(r,indent=2));print(r)
