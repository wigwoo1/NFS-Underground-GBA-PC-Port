from pathlib import Path
import json,struct
from owned_graph_packet import GraphPacket
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_scene_bundle import SceneBundle
from owned_motion_pairs import records
p=Path('work/camera');checks=[];matched=unmatched=0
for source_refresh,frame_refresh in zip((8754,8758,8762,8765,8769,8772,8776),(8758,8762,8766,8769,8773,8776,8780)):
 graph=GraphPacket.decode((p/f'graph-packets/{source_refresh}.ngp').read_bytes());sources=wall_sources(graph)+supplemental_wall_sources(SceneBundle.decode((p/f'scene-bundles/{source_refresh}.nsb').read_bytes()));frame=records((p/f'motion-actual-scanline-assets/{frame_refresh}-native-complete-frame.bin').read_bytes());scene_matched=scene_unmatched=0
 for row in frame['records']:
  if row['kind']!=2:continue
  b=row['blocks'];candidates=[w for w in sources if w.vertices==bytes(b[0])]
  if not candidates:unmatched+=1;scene_unmatched+=1;continue
  exact=[w for w in candidates if w.offsets==bytes(b[1]) and w.animation==bytes(b[2]) and w.shift==struct.unpack_from('<H',b[4],36)[0] and w.height==struct.unpack_from('<H',b[4],38)[0] and w.texture==bytes(b[8])[:len(w.texture)]]
  assert exact,(source_refresh,'raw edge payload mismatch');matched+=1;scene_matched+=1
 checks.append(dict(source_refresh=source_refresh,potential_edges=len(sources),executed_matches=scene_matched,outside_graph=scene_unmatched))
assert matched==35 and unmatched==0
r=dict(result='PASS_OWNED_GRAPH_WALL_SOURCE_PARITY',matched=matched,outside_graph=unmatched,checks=checks,scope='Raw graph edge/material ownership; Graph plus supplemental raw edges; draw flags/order/clips and GPU dispatch pending.')
(p/'owned-graph-wall-sources.json').write_text(json.dumps(r,indent=2));print(r)
