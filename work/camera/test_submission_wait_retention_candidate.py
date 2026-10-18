import json
from pathlib import Path
from owned_submission_wait_rows_candidate import SubmissionRows
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791550153527840100.json').read_text());rows=r['worker_submit_stage_samples'];owner=SubmissionRows(2)
for x in rows:owner.append(x)
stats=owner.stats()['whole_submission_space_wait'];expected=[x for x in rows if x['space_wait_ns']*16777216>280896*1000000000]
assert stats['dropped']==0 and stats['long_total']==len(expected) and stats['total_ns']==sum(x['space_wait_ns'] for x in rows)
assert len(owner.snapshot())==2 and [x['space_wait_ns'] for x in stats['records']]==[x['space_wait_ns'] for x in expected]
out=dict(result='PASS_CAPTURED_SUBMISSION_WAIT_RETENTION',captured_rows=len(rows),slow_waits=len(expected),max_wait_ms=stats['max_ns']/1e6,scope='Actual recorded submit timings retained beyond recent2window; no scheduling fix or cadence claim.')
Path('work/camera/prototype-runs/submission-wait-retention-20261009.json').write_text(json.dumps(out,indent=2));print(out)
