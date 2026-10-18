"""Captured phase/delivery audit; preserves unpaused stalls, no scanout claim."""
import json,math,sys
from pathlib import Path

def analyze(r):
 sources={(s['epoch'],s['publication']):s for s in r['sky_capture_records']}
 pauses=r['pause_events']; assert not r.get('pause_retention',{}).get('dropped_records',0)
 rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample') and x.get('sky_phase_mode')=='continuous_angle']
 checks=[]
 for x in rows:
  a=sources[x['epoch'],x['source_older']];b=sources[x['epoch'],x['refresh']]
  assert a['asset_origin']==b['asset_origin']
  delta=((b['angle']-a['angle']+8192)&16383)-8192
  angle=(b['angle']&16383) if x['alpha']==1 else (a['angle']&16383)+delta*x['alpha']
  phase=(angle*240/4096)%240
  assert math.isclose(phase-math.floor(phase),x['sky_fraction'],abs_tol=1e-10)
  checks.append((x,phase,delta))
 active=[];excluded=0
 for (a,pa,da),(b,pb,db) in zip(checks,checks[1:]):
  begin=a['native_committed_sample'][6];end=b['native_committed_sample'][6]
  paused=any(p['begin_ns']<end and p['end_ns']>begin for p in pauses)
  if paused or a['epoch']!=b['epoch'] or a['generation']!=b['generation'] or b['display_index']!=a['display_index']+1:excluded+=1;continue
  assert end>=begin
  travel=(pb-pa+120)%240-120
  active.append(dict(display_index=b['display_index'],interval_ms=(end-begin)/1e6,travel_source_pixels=travel,source_angles_stationary=da==0 and db==0))
 stationary=[x for x in active if abs(x['travel_source_pixels'])<1e-10]
 return dict(result='PASS_CAPTURED_PHASE_DELIVERY_AUDIT',samples=len(rows),active_transitions=len(active),excluded_pause_or_identity_transitions=excluded,stationary_transitions=len(stationary),stationary_with_unchanged_source_angles=sum(x['source_angles_stationary'] for x in stationary),unpaused_gaps_over_25ms=[x for x in active if x['interval_ms']>25],unpaused_gaps_over_33ms=[x for x in active if x['interval_ms']>1000/30],scope='Retained diagnostic rows only; commit intervals retain actual unpaused stalls. Source phase telemetry is not rendered pixels or physical scanout.')

if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
