import json,copy
from pathlib import Path
from owned_native_transaction_interval_totals_candidate import LongIntervalTotals
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791642761397491600.json').read_text());rows=r['presentation_samples'];assert len(rows)==120
tracker=LongIntervalTotals(capacity=2);reference=[]
for i,original in enumerate(rows):
 row=copy.deepcopy(original);row['generation']=i//20+1;tracker.observe(row)
 if i%20==0:reference.append(dict(epoch=row['epoch'],generation=row['generation'],first_success_ns=row['commit'][6],first_success_deadline_ns=row['native_transaction']['wait'][1],last_success_ns=row['commit'][6],first_index=row['display_index'],last_index=row['display_index'],successful_samples=1))
 else:reference[-1].update(last_success_ns=row['commit'][6],last_index=row['display_index'],successful_samples=reference[-1]['successful_samples']+1)
 if i==110:
  snapshot=copy.copy(tracker);frozen=snapshot.stats()['native_success_segments']
actual=tracker.stats()['native_success_segments'];assert actual['records']==reference[-2:] and actual['total']==6 and actual['dropped']==4
assert snapshot.stats()['native_success_segments']==frozen
returned=tracker.stats();returned['native_success_segments']['records'][-1]['last_index']=-1;assert tracker.stats()['native_success_segments']==actual
empty=LongIntervalTotals().stats()['native_success_segments'];assert empty['total']==empty['dropped']==0 and empty['records']==[]
result=dict(result='PASS_BOUNDED_NATIVE_SEGMENT_ACCOUNTING',rows=120,segments=6,retained=2,dropped=4,copy_isolated=True,report_isolated=True,scope='Actual retained row replay with synthetic generation boundaries, exact independent expected summaries; no live pause coverage or sustained60 proof.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/native-success-segments-component.json').write_text(json.dumps(result,indent=2));print(result)
