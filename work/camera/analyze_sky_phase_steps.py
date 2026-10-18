"""Classify captured sky motion; phase telemetry is not pixel/scanout proof."""
import json, math, sys
from pathlib import Path

def analyze(report):
 sources={(s['epoch'],s['publication']):s for s in report['sky_capture_records']}
 rows=[r for r in report['presentation_samples'] if r.get('native_committed_sample') and r.get('sky_interpolated')]
 checks=[]
 for row in rows:
  a=sources[row['epoch'],row['source_older']];b=sources[row['epoch'],row['refresh']]
  delta=((b['angle']-a['angle']+8192)&16383)-8192
  angle=(a['angle']&16383)+delta*row['alpha']
  phase=(angle*240/4096)%240
  assert abs((phase-math.floor(phase))-row['sky_fraction'])<1e-10
  checks.append((row,phase,delta))
 transitions=[]
 for (a,pa,da),(b,pb,db) in zip(checks,checks[1:]):
  if a['epoch']!=b['epoch'] or b['display_index']!=a['display_index']+1:continue
  # Exclude pause intervals using the same two-refresh diagnostic threshold.
  if b['native_committed_sample'][6]-a['native_committed_sample'][6]>33333334:continue
  travel=(pb-pa+120)%240-120
  transitions.append(dict(display_index=b['display_index'],source_pair_changed=(a['source_older'],a['refresh'])!=(b['source_older'],b['refresh']),source_angles_stationary=da==0 and db==0,travel_source_pixels=travel))
 stationary=[t for t in transitions if abs(t['travel_source_pixels'])<1e-10]
 moving=[t for t in transitions if abs(t['travel_source_pixels'])>=1e-10]
 return dict(result='PASS_PHASE_AUDIT',samples=len(rows),active_transitions=len(transitions),moving_transitions=len(moving),stationary_transitions=len(stationary),stationary_with_unchanged_source_angles=sum(t['source_angles_stationary'] for t in stationary),maximum_step_source_pixels=max((abs(t['travel_source_pixels']) for t in moving),default=0),largest_steps=sorted(moving,key=lambda t:abs(t['travel_source_pixels']),reverse=True)[:10],scope='Reconstructed captured camera-angle phase. Does not verify texture upload, visible pixels, physical scanout, or visual smoothness.')

if __name__=='__main__':
 report=Path(sys.argv[1]);output=Path(sys.argv[2]);result=analyze(json.loads(report.read_text()));output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
