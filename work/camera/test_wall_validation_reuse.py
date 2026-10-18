from pathlib import Path
import struct,time,statistics,json
from owned_graph_packet import GraphPacket
from owned_wall_projection import projected,reciprocal_table
from owned_wall_projection_validation_reference import projected as previous
p=Path('work/camera');table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[]
for file in sorted((p/'graph-packets').glob('*.ngp')):
 graph=GraphPacket.decode(file.read_bytes());expected=previous(graph,table);assert projected(graph,table)==expected;cost=[[],[]]
 for repeat in range(8):
  for index,fn in ((0,previous),(1,projected)) if repeat%2==0 else ((1,projected),(0,previous)):
   start=time.perf_counter_ns();actual=fn(graph,table);cost[index].append((time.perf_counter_ns()-start)/1e6);assert actual==expected
 before,after=map(statistics.median,cost);checks.append(dict(refresh=graph.refresh,uncached_ms=before,cached_ms=after,speedup=before/after))
assert reciprocal_table(table) is reciprocal_table(tuple(list(table)))
for bad in (table[:-1],(-1,)+table[1:]):
 try:reciprocal_table(bad)
 except ValueError:pass
 else:raise AssertionError('Invalid reciprocal accepted')
r=dict(result='PASS_REUSED_IMMUTABLE_GRAPH_VALIDATION',checks=checks,cache=reciprocal_table.cache_info()._asdict(),scope='Exact scratch/selection/stat parity and alternating same-input component cost; bounded immutable content-keyed table, invalid inputs reject. Not fullscene60fps proof.')
(p/'owned-wall-validation-reuse.json').write_text(json.dumps(r,indent=2));print(r)

from dataclasses import replace
from owned_wall_projection import validated_graph
assert validated_graph(graph) is graph
try: validated_graph(replace(graph,context=graph.context[:-1]))
except ValueError: pass
else: raise AssertionError('Corrupt graph accepted by cached validation')
assert validated_graph.cache_info().currsize<=2
