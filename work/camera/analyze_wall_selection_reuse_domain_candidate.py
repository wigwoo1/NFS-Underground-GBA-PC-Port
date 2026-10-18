import json
from pathlib import Path
import owned_sampled_graph_wall_visibility as selection
original=selection.wall_region_candidates
calls=[]
def candidates(portal,alpha,*,queue=None):
 result=original(portal,alpha,queue=queue)
 calls.append(dict(alpha=alpha,explicit_queue=queue is not None,queue=None if queue is None else [list(x) for x in queue],keys=[(x.descriptor,x.edge) for x in result]))
 return result
selection.wall_region_candidates=candidates
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace('from owned_prepared_world_motion import PreparedWorldMotion','from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
exec(compile(source,'captured_scene_setup','exec'))
try:
 for i in range(1,100):prepared.sample(i/100)
 rows=[]
 for i in range(1,100):
  alpha=i/100;subset=[x for x in calls if x['alpha']==alpha];main=[x for x in subset if not x['explicit_queue']];child=[x for x in subset if x['explicit_queue']];assert len(main)==1
  mainkeys=set(main[0]['keys']);childkeys=set(k for x in child for k in x['keys'])
  rows.append(dict(alpha=alpha,selection_calls=len(subset),main_candidates=len(mainkeys),child_candidates=len(childkeys),shared_edge_keys=len(mainkeys&childkeys),child_queues=[x['queue'] for x in child]))
 out=dict(result='PASS_ACTUAL_WALL_SELECTION_DOMAINS',samples=len(rows),calls=len(calls),total_shared_edge_keys=sum(x['shared_edge_keys'] for x in rows),rows=rows,scope='One captured static-child scene pair, 99 poses; exact main versus explicit child descriptor/edge domains. Shared edge keys alone do not prove equal projection inputs or bounds.')
 Path('work/camera/prototype-runs/wall-selection-reuse-domain.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});print(rows[0])
finally:prepared.close();history.close();selection.wall_region_candidates=original
