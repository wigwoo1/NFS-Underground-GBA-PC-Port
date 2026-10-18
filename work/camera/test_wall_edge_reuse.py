"""Reuse camera-space edges; recompute clipping for every region."""
from pathlib import Path
from unittest.mock import patch
import owned_sampled_graph_wall_visibility as walls
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
exec(compile(source,'captured_scene_setup','exec'))
portal=prepared.pair.portal;original=walls.sampled_edge
try:
 queue=portal.sample(.5)
 with patch.object(walls,'sampled_edge',wraps=original) as measured:
  first=walls.selected_graph_walls(portal,.5,queue=queue);count=measured.call_count
  assert count>0
  second=walls.selected_graph_walls(portal,.5,queue=queue)
  assert first==second and measured.call_count==count*2
  narrowed=tuple((q[0],q[1]+1,q[2]-1,q[3],q[4],*q[5:]) for q in queue)
  reused=walls.selected_graph_walls(portal,.5,queue=narrowed)
  assert measured.call_count>=count*2
 assert reused==walls.selected_graph_walls(portal,.5,queue=narrowed)
 for alpha in (0,1,.1,.2,.3,.4,.6,.7,.8,.9):walls.selected_graph_walls(portal,alpha)
 assert not hasattr(portal,'_wall_edge_samples')
 print('PASS: deterministic edges, region clipping recomputed, exact output equality, no ineffective edge cache')
finally:prepared.close();history.close()
