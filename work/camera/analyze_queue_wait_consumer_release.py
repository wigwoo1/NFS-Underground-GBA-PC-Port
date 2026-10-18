"""Bounded queue wait/dequeue joins; does not infer stalled rendering."""
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());q=d['submit_retention']['whole_submission_space_wait'];c=d['boundary_retention']['complete_dequeues'];l=d['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']
assert q['dropped']==0 and c['dropped']==0 and c['total']==len(c['records']) and l['dropped']==0
out=[]
for refresh in [12803,12627]:
 s=next(x for x in q['records'] if x['scene_identity'][1]==refresh);a=s['submit_begin_ns'];b=a+s['space_wait_ns']
 pops=[x for x in c['records'] if a<=x['popped_ns']<=b];assert len(pops)==1;p=pops[0]
 overlaps=[x for x in l['records'] if x['begin_ns']<b and x['end_ns']>a]
 out.append(dict(submission_refresh=refresh,queue_wait_ms=(b-a)/1e6,released_source_refresh=p['refresh'],pop_to_admission_ms=(b-p['popped_ns'])/1e6,source_age_at_pop_ms=(p['popped_ns']-p['source_submitted_ns'])/1e6,overlapping_native_long_intervals=len(overlaps),max_overlapping_native_gap_ms=max([x['interval_ns']/1e6 for x in overlaps],default=None)))
r=dict(result='PASS_QUEUE_WAIT_CONSUMER_POP_JOINS',rows=out,scope='Exact source submission and one consumer pop within admission wait; source age is elapsed queue/history age, not proof of clock drift. Complete native long ledger supplies overlap counts, not every presentation or scanout. Native capacity release itself is inferred from inspected pop path, not independently instrumented.')
Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print(json.dumps(r))
