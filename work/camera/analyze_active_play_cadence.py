"""Separate recorded intentional pause intervals; preserve raw cadence evidence."""
import json,sys,statistics
from pathlib import Path

def analyze(report):
 if report.get('bounded_diagnostic_stats',{}).get('dropped_records',0):raise ValueError('Whole-run cadence unavailable: presentation telemetry truncated')
 pauses=sorted(report.get('pause_events',[]),key=lambda x:x['begin_ns'])
 for i,p in enumerate(pauses):
  assert p['end_ns']>=p['begin_ns'] and p['duration_ns']==p['end_ns']-p['begin_ns']
  if i:assert pauses[i-1]['end_ns']<=p['begin_ns']
 rows=[r for r in report['presentation_samples'] if r.get('interpolated') and r.get('hidden_window_presented')]
 gaps=[];excluded=[]
 for a,b in zip(rows,rows[1:]):
  begin=a['callback_timing']['present_end_ns'] if a.get('native_deadline_path') else a['present_end_ns']
  end=b['callback_timing']['present_end_ns'] if b.get('native_deadline_path') else b['present_end_ns']
  gap=end-begin;assert gap>=0
  overlap=sum(max(0,min(end,p['end_ns'])-max(begin,p['begin_ns'])) for p in pauses)
  if overlap:excluded.append(dict(display_index=b['display_index'],raw_gap_ms=gap/1e6,recorded_pause_overlap_ms=overlap/1e6,nonpause_residual_ms=(gap-overlap)/1e6))
  # Retain all unpaused time, including stalls before/after a pause boundary.
  gaps.append((gap-overlap)/1e6)
 wall=report['timing']['wall_seconds'];pause=sum(p['duration_ns'] for p in pauses)/1e9;assert wall>pause
 return dict(scope='CPU presentation gaps minus only recorded intentional pause overlap; nonpause residuals retained including boundary stalls; no scanout certification',active_clock_ratio=report['timing']['simulated_seconds']/(wall-pause),pause_seconds=pause,contiguous=all(b['display_index']==a['display_index']+1 for a,b in zip(rows,rows[1:])),active_gap_count=len(gaps),active_gap_median_ms=statistics.median(gaps) if gaps else None,active_gap_p95_ms=sorted(gaps)[int(.95*(len(gaps)-1))] if gaps else None,active_gap_max_ms=max(gaps) if gaps else None,active_gaps_over_two_refreshes=sum(g>1000/30 for g in gaps),excluded_pause_crossings=excluded)
if __name__=='__main__':
 p=Path(sys.argv[1]);result=analyze(json.loads(p.read_text()));p.with_suffix('.active-cadence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
