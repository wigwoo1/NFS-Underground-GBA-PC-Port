"""Audit retained live sky phases separately from whole-run counters and pixels."""
import json, math, sys
from pathlib import Path

def audit(r):
 assert r['status']=='SMOKE_COMPLETE' if 'status' in r else not r.get('error')
 totals=r['bounded_diagnostic_stats']['whole_run_sky_motion']
 assert totals['successful_samples'] >= 2
 assert totals['adjacent_transitions'] + totals['excluded_identity_discontinuities'] == totals['successful_samples'] - 1
 assert 0 <= totals['stationary_transitions'] <= totals['adjacent_transitions']
 assert 0 <= totals['commit_intervals_over_25ms'] <= totals['adjacent_transitions']
 assert 0 <= totals['api_intervals_over_25ms'] <= totals['adjacent_transitions']
 rows=r['presentation_samples']
 checked=transitions=held=source_holds=moving=0
 previous=None
 for row in rows:
  if row['native_result']!=1:continue
  assert row['sky_phase_mode']=='continuous_angle'
  a,b=row['sky_source_angles'];alpha=row['alpha']
  assert math.isfinite(alpha) and 0<=alpha<=1
  delta=((b-a+8192)&16383)-8192
  assert abs(delta*240/4096)<120
  phase=(((b&16383) if alpha==1 else (a&16383)+delta*alpha)*240/4096)%240
  assert math.isclose(row['sky_fraction'],phase-math.floor(phase),rel_tol=0,abs_tol=1e-10)
  key=(row['epoch'],row['generation'],row['display_index'])
  if previous:
   pk,pp,pd=previous
   if key[:2]==pk[:2] and key[2]==pk[2]+1:
    transitions+=1
    stationary=abs((phase-pp+120)%240-120)<1e-10
    held+=stationary
    source_holds+=stationary and delta==0 and pd==0
    moving+=not stationary
  previous=key,phase,delta;checked+=1
 assert checked and held==source_holds,'Held phase despite moving source angles'
 assert totals['stationary_transitions']==totals['stationary_with_unchanged_source_angles']
 return dict(result='PASS_CAPTURED_PHASE_ATTRIBUTION',whole_run=totals,
  retained_window=dict(samples=checked,adjacent=transitions,held=held,unchanged_source_holds=source_holds,moving=moving),
  scope='Captured phase metadata only. Whole-run counters are distinguished from the retained 120-row window. No live rendered pixel, physical scanout, or independent camera fidelity proof.')
if __name__=='__main__':
 source=Path(sys.argv[1]);r=json.loads(source.read_text());result=audit(r)
 import copy
 bad=copy.deepcopy(r);bad['presentation_samples'][-1]['sky_fraction']+=.1
 try:audit(bad)
 except AssertionError:result['corrupted_fraction_rejected']=True
 else:raise AssertionError('Corrupt phase accepted')
 bad=copy.deepcopy(r);bad['bounded_diagnostic_stats']['whole_run_sky_motion']['adjacent_transitions']+=1
 try:audit(bad)
 except AssertionError:result['corrupted_whole_run_count_rejected']=True
 else:raise AssertionError('Corrupt whole-run transition count accepted')
 result['source']=str(source.resolve())
 Path(sys.argv[2]).write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
