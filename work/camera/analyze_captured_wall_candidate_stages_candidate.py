import os,json,statistics
from pathlib import Path
os.environ['NFSUG_WALL_CANDIDATE_TRACE']='1'
import owned_sampled_graph_wall_visibility as selection
original=selection.wall_region_candidates;calls=[]
def collect(portal,alpha,*,queue=None):
 result=original(portal,alpha,queue=queue);rows=list(portal._last_wall_candidate_stages)
 for row in rows:assert row['wall_ns']==row['completed_ns']-row['started_ns'] and row['wall_ns']>=0
 calls.append(dict(alpha=alpha,child=queue is not None,candidates=len(result),stages=rows));return result
selection.wall_region_candidates=collect
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace('from owned_prepared_world_motion import PreparedWorldMotion','from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
exec(compile(source,'captured_scene_setup','exec'))
try:
 for i in range(1,100):prepared.sample(i/100)
 summaries=[]
 for child in (False,True):
  selected=[x for x in calls if x['child']==child];assert selected
  names=[x['name'] for x in selected[0]['stages']]
  values={name:[next(x['wall_ns']/1e6 for x in call['stages'] if x['name']==name) for call in selected] for name in names}
  summaries.append(dict(child=child,calls=len(selected),stages_ms={name:dict(first=v[0],median=statistics.median(v),maximum=max(v),total=sum(v)) for name,v in values.items()}))
 out=dict(result='PASS_CAPTURED_WALL_CANDIDATE_STAGE_PARTITIONS',summary=summaries,calls=calls,scope='One captured static-child scene pair,99poses; explicit main/child separation and stage boundaries. Cold first call separated from warm medians; observer affects timing and this is not live cadence qualification.')
 Path('work/camera/prototype-runs/captured-wall-candidate-stages.json').write_text(json.dumps(out,indent=2));print(json.dumps(summaries))
finally:prepared.close();history.close();selection.wall_region_candidates=original
