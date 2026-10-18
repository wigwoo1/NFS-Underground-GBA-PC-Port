import json,copy
from owned_producer_slow_ledger_candidate import ProducerDeadlineRows
from analyze_slow_producer_gc_candidate import analyze,overlap
r=json.load(open('work/camera/prototype-runs/owned-native-1791532056300918200.json'));q=ProducerDeadlineRows()
for x in r['original_update_samples']:q.append(x)
r['original_updates']=len(r['original_update_samples']);r['original_update_retention']=q.stats();o=analyze(r)
assert o['count']==q.over_two_periods
assert overlap(0,20,[dict(start_ns=2,end_ns=12),dict(start_ns=5,end_ns=15)])==13
for change in ('drop','gc','count','deadline'):
 z=copy.deepcopy(r)
 if change=='drop':z['original_update_retention']['slow_original_updates']['dropped']=1
 elif change=='gc':z['gc_trace_dropped']=1
 elif change=='count':z['original_updates']+=1
 else:
  assert z['original_update_retention']['slow_original_updates']['records']
  z['original_update_retention']['slow_original_updates']['records'][0]['original_deadline_ns']-=1
 try:analyze(z)
 except AssertionError:pass
 else:raise AssertionError('Invalid '+change+' evidence accepted')
print('PASS_SLOW_PRODUCER_ACTUAL_ROWS_AND_INCOMPLETE_EVIDENCE_REJECTION')
