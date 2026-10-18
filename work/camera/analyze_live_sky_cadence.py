"""Separate captured stationary sky phase from presentation cadence stalls.

Host telemetry cannot certify physical display scanout or visual fidelity.
"""
import json, math, sys
from pathlib import Path
from verify_live_sky_motion_evidence import verify

def analyze(report):
 audit=verify(report)
 assert report.get('sky_continuous_enabled'), 'Requires continuous sky source telemetry'
 sources={(s['epoch'],s['publication']):s for s in report['sky_capture_records']}
 rows=[x for x in report['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')]
 samples=[]
 for row in rows:
  a=sources[row['epoch'],row['source_older']]['angle']
  b=sources[row['epoch'],row['refresh']]['angle']
  delta=((b-a+8192)&16383)-8192
  angle=(b&16383) if row['alpha']==1 else (a&16383)+delta*row['alpha']
  samples.append(dict(display_index=row['display_index'],epoch=row['epoch'],older=row['source_older'],newer=row['refresh'],alpha=row['alpha'],phase=(angle*240/4096)%240,source_delta=delta,committed_ns=row['native_committed_sample'][6]))
 moving_pairs=stationary_pairs=0; frozen=[]; gaps=[]
 for previous,current in zip(samples,samples[1:]):
  if previous['epoch']!=current['epoch']:continue
  same_pair=(previous['older'],previous['newer'])==(current['older'],current['newer'])
  if same_pair and current['alpha']!=previous['alpha']:
   if current['source_delta']:
    moving_pairs+=1
    if math.isclose(previous['phase'],current['phase'],rel_tol=0,abs_tol=1e-10):frozen.append(current['display_index'])
   else:stationary_pairs+=1
  gap=(current['committed_ns']-previous['committed_ns'])/1e6
  if gap>1000/30:
   gaps.append(dict(display_index=current['display_index'],gap_ms=gap,phase_travel=((current['phase']-previous['phase']+120)%240)-120))
 assert not frozen, 'Sky phase frozen within moving source pair'
 return dict(result='PASS_CAPTURED_SKY_MOTION',samples=len(samples),moving_same_pair_transitions=moving_pairs,stationary_same_pair_transitions=stationary_pairs,frozen_moving_transitions=frozen,raw_commit_gaps_over_two_refreshes=len(gaps),largest_raw_commit_gaps=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True)[:12],active_presentation_cadence=audit['cadence'],cpu_cadence_gate=audit['cpu_cadence_gate'],scope='Captured angle phase and native commit times; raw commit gaps include intentional pauses. Active cadence subtracts only recorded pause overlap and retains unpaused boundary stalls. No physical scanout or independent image fidelity certification.')

if __name__=='__main__':
 source=Path(sys.argv[1]);result=analyze(json.loads(source.read_text()))
 output=Path(sys.argv[2]) if len(sys.argv)>2 else source.with_suffix('.sky-cadence.json')
 output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
