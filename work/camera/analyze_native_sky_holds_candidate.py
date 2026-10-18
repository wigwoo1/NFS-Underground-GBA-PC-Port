"""Correlate captured native sky phase holds with source angles and API gaps."""
import json,math,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());sources={(x['epoch'],x['publication']):x for x in r['sky_capture_records']};rows=[x for x in r['presentation_samples'] if x['native_result']==1];previous=None;holds=[];gaps=[]
for x in rows:
 a=sources[x['epoch'],x['source_older']];b=sources[x['epoch'],x['refresh']];delta=((b['angle']-a['angle']+8192)&16383)-8192;angle=(b['angle']&16383) if x['alpha']==1 else (a['angle']&16383)+delta*x['alpha'];phase=angle*240/4096%240
 assert math.isclose(x['sky_fraction'],phase-math.floor(phase),abs_tol=1e-10)
 if previous:
  p,pa,pp=previous
  if x['display_index']==p['display_index']+1 and x['generation']==p['generation'] and x['epoch']==p['epoch']:
   if abs(phase-pp)<1e-10:holds.append(dict(index=x['display_index'],older=a['angle'],newer=b['angle'],source_delta=delta,previous_sample_angle=pa,sample_angle=angle))
   interval=(x['callback_timing']['present_end_ns']-p['callback_timing']['present_end_ns'])/1e6
   if interval>25:gaps.append(dict(index=x['display_index'],interval_ms=interval,deadline_lateness_ms=(x['callback_timing']['present_end_ns']-x['presentation_deadline_ns'])/1e6,draw_ms=(x['callback_timing']['draw_end_ns']-x['callback_timing']['draw_begin_ns'])/1e6,present_ms=(x['callback_timing']['present_end_ns']-x['callback_timing']['present_begin_ns'])/1e6,pair_changed=(x['source_older'],x['refresh'])!=(p['source_older'],p['refresh'])))
 previous=x,angle,phase
out=dict(result='CAPTURED_SKY_HOLD_AND_GAP_ANALYSIS',samples=len(rows),holds=len(holds),holds_with_zero_source_delta=sum(x['source_delta']==0 for x in holds),holds_with_moving_source_delta=sum(x['source_delta']!=0 for x in holds),gaps_over_25ms=len(gaps),gaps_at_pair_boundary=sum(x['pair_changed'] for x in gaps),hold_records=holds,gap_records=gaps,scope='Captured continuous phase and CPU/API times, not live pixel or scanout evidence.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if not k.endswith('_records')})
