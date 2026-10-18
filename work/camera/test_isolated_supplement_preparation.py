from pathlib import Path
import json,struct,time,statistics
from owned_scene_bundle import SceneBundle,chunks
from owned_graph_packet import GraphPacket
from owned_graph_wall_sources import supplemental_wall_sources
from owned_wall_projection_selected_reference import projected as previous
from owned_wall_projection import projected
p=Path('work/camera');reciprocal=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);checks=[]
for file in sorted((p/'scene-bundles').glob('*.nsb')):
 bundle=SceneBundle.decode(file.read_bytes());graph=GraphPacket.decode(bundle.graph);sources=supplemental_wall_sources(bundle)
 for h,raw in chunks(bundle.supplements,'supplements'):
  ring=b''.join(raw[976+i*140:1044+i*140] for i in range(h[4]));points=[ring[i*68:(i+1)*68] for i in range(h[4])];subset=[w for w in sources if w.descriptor==h[3] and w.vertices[:68] in points];supp=(raw,subset)
  expected=previous(graph,reciprocal,supp);assert projected(graph,reciprocal,supp)==expected;costs=[[],[]]
  for repeat in range(8):
   for index,fn in ((0,previous),(1,projected)) if repeat%2==0 else ((1,projected),(0,previous)):
    began=time.perf_counter_ns();actual=fn(graph,reciprocal,supp);costs[index].append((time.perf_counter_ns()-began)/1e6);assert actual==expected
  before,after=map(statistics.median,costs);checks.append(dict(scene=file.name,descriptor=h[3],draws=len(expected[0]),previous_median_ms=before,isolated_median_ms=after,speedup=before/after))
assert len(checks)==9
r=dict(result='PASS_ISOLATED_SUPPLEMENT_PREPARATION',checks=checks,scope='Same-input alternating component benchmark; exact source selection/scratch/stats and graph validation retained. Not full-scene60fps proof.')
(p/'owned-supplement-preparation-cost.json').write_text(json.dumps(r,indent=2));print(r)
