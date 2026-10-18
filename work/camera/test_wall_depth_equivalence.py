from pathlib import Path
from unittest.mock import patch
import owned_continuous_wall_visibility as visibility
import owned_sampled_graph_wall_visibility as walls
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
exec(compile(source,'captured_scene_setup','exec'))
old=Path('work/camera/owned_continuous_wall_visibility.py').read_text().replace(' depth=projection_depth(z,scale,reciprocal);next_depth=projection_depth(nz,scale,reciprocal)\n left,right=coordinate_at_depth(x,depth,cx),coordinate_at_depth(nx,next_depth,cx)',' left,right=coordinate(x,z,scale,cx,reciprocal),coordinate(nx,nz,scale,cx,reciprocal)').replace(' y=tuple(coordinate_at_depth(v,depth if i%2==0 else next_depth,cy) for i,v in enumerate(ys))',' y=tuple(coordinate(v,z if i%2==0 else nz,scale,cy,reciprocal) for i,v in enumerate(ys))')
namespace={};exec(compile(old,'prior_wall_projection','exec'),namespace)
try:
 for i in range(101):
  alpha=i/100
  current=walls.selected_graph_walls(prepared.pair.portal,alpha)
  with patch.object(walls,'select_wall',namespace['select_wall']):reference=walls.selected_graph_walls(prepared.pair.portal,alpha)
  assert [(c,v.visible,v.reason,v.x,v.y,v.flags) for c,v in current]==[(c,v.visible,v.reason,v.x,v.y,v.flags) for c,v in reference]
 print('PASS:101 captured wall selections exact old/new candidates, clipping, projected positions and flags')
finally:prepared.close();history.close()
