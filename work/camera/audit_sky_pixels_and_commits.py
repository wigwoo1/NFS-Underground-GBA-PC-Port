"""Attribute sampled sky-stage/final pixels to committed frames; diagnostic only."""
import json,sys
from pathlib import Path

def analyze(report, diagnostic):
 committed={r['display_index']:r for r in report['presentation_samples'] if r.get('native_committed_sample')}
 rows=diagnostic['records']; checks=[]
 for row in rows:
  assert 'error' not in row
  c=committed[row['display_index']]
  for key in ('epoch','source_older','refresh','alpha'):assert row[key]==c[key],key
  assert row['selected_epoch']==c['epoch'] and row['thread']==c['consumer_thread']
  points=row['sky_reference_points']
  assert all(len(p[k])==3 for p in points for k in ('actual','expected','stage'))
  assert all(max(abs(a-b) for a,b in zip(p['stage'],p['expected']))<=1 for p in points),'Sky stage differs from reference'
 for a,b in zip(rows,rows[1:]):
  if a['epoch']!=b['epoch'] or b['display_index']!=a['display_index']+1:continue
  assert [(p['x'],p['y']) for p in a['sky_reference_points']]==[(p['x'],p['y']) for p in b['sky_reference_points']]
  pairs=list(zip(a['sky_reference_points'],b['sky_reference_points']))
  expected=sum(x['expected']!=y['expected'] for x,y in pairs)
  stage=sum(x['stage']!=y['stage'] for x,y in pairs)
  final=sum(x['actual']!=y['actual'] for x,y in pairs)
  assert not expected or stage,'Repeated sky stage despite changing reference'
  gap=(committed[b['display_index']]['native_committed_sample'][6]-committed[a['display_index']]['native_committed_sample'][6])/1e6
  checks.append(dict(previous=a['display_index'],current=b['display_index'],commit_gap_ms=gap,over_two_refreshes=gap>1000/30,expected_changed_points=expected,stage_changed_points=stage,final_changed_points=final,final_points_near_sky_reference=sum(max(abs(v-w) for v,w in zip(y['actual'],y['expected']))<=1 for x,y in pairs)))
 return dict(result='PASS_ATTRIBUTED_SKY_STAGE',sampled_frames=len(rows),adjacent_transitions=len(checks),moving_stage_transitions=sum(x['stage_changed_points']>0 for x in checks),diagnostic_gaps_over_two_refreshes=sum(x['over_two_refreshes'] for x in checks),transitions=checks,scope='Synchronous selected-target readback affects cadence; final points may be occluded. Commit intervals include pauses and are diagnostic only. No physical scanout or sustained gameplay certification.')

if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))
 Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='transitions'},indent=2))
