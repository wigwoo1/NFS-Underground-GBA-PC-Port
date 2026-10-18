import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());groups={}
for x in r['presentation_samples']:
 if x.get('native_committed_sample'):groups.setdefault(x['batch_native_call_ns'],[]).append(x)
checks=0
for batch in groups.values():
 rows=sorted(batch,key=lambda x:x['batch_sample_position'])
 for a,b in zip(rows,rows[1:]):
  assert a['native_committed_sample'][6]<=b['queued_stage_timing'][0];checks+=1
assert checks>0
from analyze_active_play_cadence import analyze
c=analyze(r)
out=dict(result='PASS_LIVE_SINGLE_FRAME_ORDER',groups=len(groups),adjacent_checks=checks,cadence=c,scope='Recorded committed timestamp precedes next draw in each batch; CPU evidence only, not visual/physicalscanout or performance causality.')
Path('work/camera/queued-single-live-order.json').write_text(json.dumps(out,indent=2));print(checks,c['active_gaps_over_two_refreshes'],c['active_gap_max_ms'],c['active_gap_p95_ms'])

