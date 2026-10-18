"""Actual retained original-update timeline near the late-race stall."""
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());ledger=r['original_update_retention']['slow_original_updates'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
unique={}
for row in r['original_update_samples']+ledger['records']:
 key=(row['clock_origin'],row['refresh'])
 if key in unique:assert row==unique[key]
 unique[key]=row
rows=sorted([x for x in unique.values() if 12180<=x['refresh']<=12188],key=lambda x:x['refresh']);assert [x['refresh'] for x in rows]==list(range(12180,12189))
checks=[]
for row in rows:
 a,b,cycles,*_=row['native_boundary'];start,end=row['started_ns'],row['completed_ns'];assert start<=a<=b<=end
 prior=row['preceding_caller'];assert prior['previous_completed_ns']<=prior['submit_begin_ns']<=prior['submit_end_ns']<=start
 checks.append(dict(refresh=row['refresh'],original_update_ms=(end-start)/1e6,native_elapsed_ms=(b-a)/1e6,native_thread_cycles=cycles,start_lateness_ms=(start-row['original_deadline_ns'])/1e6,completion_lateness_ms=(end-row['original_deadline_ns'])/1e6,preceding_submission_ms=(prior['submit_end_ns']-prior['submit_begin_ns'])/1e6,post_submission_to_update_ms=(start-prior['submit_end_ns'])/1e6))
out=dict(result='PASS_COMPLETE_RETAINED_LATE_UPDATE_SEQUENCE',updates=checks,scope='Exact original-update native boundary/deadline and preceding submission timestamps for nine contiguous retained refreshes. Thread cycles not converted to CPU time; variable clock/scheduling/native waits unseparated. No game acceleration or scene smoothness proof.')
p.with_name(p.stem+'-late-original-update-audit.json').write_text(json.dumps(out,indent=2));print(out['result']);print(checks[2:4])
