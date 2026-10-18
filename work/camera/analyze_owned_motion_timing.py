"""Measure observed motion cadence without claiming physical-display fidelity."""
from pathlib import Path
import json,statistics,sys
p=Path(sys.argv[1]);r=json.loads(p.read_text());all_samples=r['presentation_samples'];s=[x for x in all_samples if x.get('interpolated')]
if not s:raise ValueError('No interpolated presentation samples')
l=[(x['present_begin_ns']-x['presentation_deadline_ns'])/1e6 for x in s]
i=[(b['present_begin_ns']-a['present_begin_ns'])/1e6 for a,b in zip(s,s[1:])]
def summary(values):
 ordered=sorted(values)
 return dict(median=statistics.median(values),minimum=min(values),maximum=max(values),p95=ordered[min(len(ordered)-1,int(len(ordered)*.95))])
a=dict(samples=len(s),initial_endpoint_samples=len(all_samples)-len(s),all_gpu_completed=all(x.get('gpu_completed_before_present',False) for x in s),all_commits_presented=all(x['hidden_window_presented'] for x in s),consecutive_display_indices=all(b['display_index']==a['display_index']+1 for a,b in zip(s,s[1:])),lateness_ms=summary(l),late_over_one_frame=sum(x>1000/60 for x in l),interval_ms=summary(i) if i else None,original_clock_timing=r['timing'],scope='Observed scripted presentation submission and optional GPU completion. Does not prove physical display cadence, full-scene interpolation correctness or controller response.')
if all('pair_ready_ns' in x for x in s):
 first={}
 for x in s:first.setdefault((x['epoch'],x['refresh']),x)
 a['source_pair_readiness']=dict(pairs=len(first),first_deadline_already_missed=sum(x['pair_ready_ns']>x['presentation_deadline_ns'] for x in first.values()),readiness_lateness_ms=summary([(x['pair_ready_ns']-x['presentation_deadline_ns'])/1e6 for x in first.values()]),scope='Pair ready on consumer before sampling/draw/wait; positive value means first deadline already missed.')
if all('source_submitted_ns' in x for x in s):
 first={}
 for x in s:first.setdefault((x['epoch'],x['refresh']),x)
 a['source_handoff']=dict(pairs=len(first),submitted_after_first_deadline=sum(x['source_submitted_ns']>x['presentation_deadline_ns'] for x in first.values()),submission_lateness_ms=summary([(x['source_submitted_ns']-x['presentation_deadline_ns'])/1e6 for x in first.values()]),queue_wait_ms=summary([(x['source_dequeued_ns']-x['source_submitted_ns'])/1e6 for x in first.values()]),scope='Timestamp after successful native push; signal/dequeue timestamps are Python scheduling observations.')
p.with_suffix('.motion-timing.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
