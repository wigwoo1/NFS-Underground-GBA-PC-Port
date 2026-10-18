import json,copy
from pathlib import Path
from owned_validated_bounded_diagnostics_candidate import ValidatedPresentationDiagnostics
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791502761374205500.json').read_text());rows=report['presentation_samples']
r=ValidatedPresentationDiagnostics(report['producer_thread_id'],report['shutdown_evidence']['context_creation_base'],max_records=3,max_bytes=65536)
for row in rows:r.append(copy.deepcopy(row))
stats=r.finalize(len(rows));assert stats['successful_presentations']==3560 and stats['unsuccessful_presentations']==3 and stats['retained_records']==3 and stats['validated_records']==3563
assert list(r)==rows[-3:]
rejected=[]
for mutation in ('thread','context','commit','expected_count'):
 v=ValidatedPresentationDiagnostics(report['producer_thread_id'],0,max_records=1,max_bytes=65536);row=copy.deepcopy(rows[0])
 if mutation=='thread':row['consumer_thread']=report['producer_thread_id']
 elif mutation=='context':row['context_count']=99
 elif mutation=='commit':row['native_committed_sample']=None
 v.append(row)
 try:v.finalize(2 if mutation=='expected_count' else 1)
 except ValueError:rejected.append(mutation)
 else:raise AssertionError(mutation)
out=dict(result='PASS_WHOLE_RUN_BOUNDED_VALIDATION',stats=stats,rejected=rejected,scope='Actual captured report replay and corruption checks; live integration pending.')
Path('work/camera/prototype-runs/native-validated-bounded-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
