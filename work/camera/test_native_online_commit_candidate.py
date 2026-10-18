import copy,json
from pathlib import Path
from owned_validated_bounded_diagnostics_candidate import ValidatedPresentationDiagnostics
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791502761374205500.json').read_text());base=next(x for x in r['presentation_samples'] if x['native_result']==1);rejected=[]
for kind in ('identity','alpha','timestamp','status','stage'):
 row=copy.deepcopy(base)
 if kind=='identity':row['native_committed_sample'][2]+=1
 elif kind=='alpha':row['alpha']+=.01
 elif kind=='timestamp':row['native_committed_sample'][6]=0
 elif kind=='status':row['presentation']['status']=3
 else:row['stages'][4]=0
 v=ValidatedPresentationDiagnostics(r['producer_thread_id'],0,max_records=1,max_bytes=65536);v.append(row)
 try:v.finalize()
 except ValueError:rejected.append(kind)
 else:raise AssertionError(kind)
out=dict(result='PASS_ONLINE_COMMIT_REJECTIONS',rejected=rejected,scope='Corrupted captured native commit metadata rejected before eviction; no pixel proof.')
Path('work/camera/prototype-runs/native-online-commit-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
