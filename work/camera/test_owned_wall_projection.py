from pathlib import Path
import json,struct
from owned_graph_packet import GraphPacket
from owned_wall_projection import projected
from owned_motion_pairs import records
p=Path('work/camera');raw=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(raw)//4)+'I',raw);checks=[]
for file in sorted((p/'graph-packets').glob('*.ngp')):
 graph=GraphPacket.decode(file.read_bytes());draws,stats=projected(graph,table)
 assert len(draws)==stats['visible'];assert all(len(row[3])==52 and not struct.unpack_from('<H',row[3],48)[0]&4 for row in draws)
 frame_refresh={8754:8758,8758:8762,8762:8766,8765:8769,8769:8773,8772:8776,8776:8780}.get(graph.refresh)
 if frame_refresh:
  captured=[bytes(row['blocks'][0]) for row in records((p/f'motion-actual-scanline-assets/{frame_refresh}-native-complete-frame.bin').read_bytes())['records'] if row['kind']==2]
  selected=[row[2].vertices for row in draws];assert all(captured.count(v)==selected.count(v) for v in selected),(graph.refresh,'Edge selection mismatch')
  assert len(captured)-len(selected)==(1 if graph.refresh==8754 else 0)
 checks.append(dict(refresh=graph.refresh,stats=stats,executed_graph_selection_exact=bool(frame_refresh)))
r=dict(result='OWNED_WALL_CLIP_PROJECT_PIPELINE_RUN',checks=checks,scope='Owned transform/heights/material UV plus ARM-verified clip/project helpers. Stage execution only; Exact executed graph wall identity/multiplicity across seven scenes; supplemental edge and final ordering pending.')
(p/'owned-wall-projection.json').write_text(json.dumps(r,indent=2));print(r)

