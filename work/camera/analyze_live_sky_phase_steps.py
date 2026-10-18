"""Measure recorded sky phase changes; does not prove rendered pixels or scanout."""
import json,math,sys,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); sources={(s['epoch'],s['publication']):s for s in r['sky_capture_records']}
rows=[s for s in r['presentation_samples'] if s.get('native_committed_sample') and s.get('sky_phase_mode')=='continuous_angle'];assert rows
counts=collections.Counter(); steps=[]
previous=None
for s in rows:
 a=sources[s['epoch'],s['source_older']];b=sources[s['epoch'],s['refresh']]
 delta=((b['angle']-a['angle']+8192)&16383)-8192
 phase=(((a['angle']&16383)+delta*s['alpha'])*240/4096)%240
 assert math.isclose(phase-math.floor(phase),s['sky_fraction'],abs_tol=1e-10)
 if previous and previous[0]['epoch']==s['epoch']:
  old,old_phase=previous;step=((phase-old_phase+120)%240)-120
  same_pair=(old['source_older'],old['refresh'])==(s['source_older'],s['refresh'])
  key=('within_pair_' if same_pair else 'pair_boundary_')+('moving' if abs(step)>1e-10 else 'stationary')
  counts[key]+=1
  if same_pair and delta and s['alpha']!=old['alpha']:assert abs(step)>1e-10,'Moving camera phase held within pair'
  if abs(step)>1e-10:steps.append(abs(step))
 previous=s,phase
out=dict(result='PASS_RECORDED_PHASE_MOTION',samples=len(rows),counts=dict(counts),maximum_phase_step_pixels=max(steps,default=0),scope='Captured camera-to-sample fractional phase only. Stationary camera may legitimately hold sky. No rendered pixel, source asset fidelity or physical display proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
