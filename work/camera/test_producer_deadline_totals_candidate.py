import json,copy
from owned_producer_deadline_totals_candidate import ProducerDeadlineRows
r=json.load(open('work/camera/prototype-runs/owned-native-1791531793462803000.json'))
rows=r['original_update_samples'];q=ProducerDeadlineRows()
for x in rows:q.append(x)
s=q.stats()['whole_run_original_deadlines'];assert s['count']==len(rows)
assert s['total_ns']['post_native_ns']==sum(x['completed_ns']-x['native_boundary'][1] for x in rows)
assert s['max_ns']['post_native_ns']==max(x['completed_ns']-x['native_boundary'][1] for x in rows)
bad=copy.deepcopy(rows[-1]);bad['native_boundary'][1]=bad['completed_ns']+1
try:q.append(bad)
except AssertionError:pass
else:raise AssertionError('Invalid boundary accepted')
assert q.stats()['whole_run_original_deadlines']['count']==len(rows)
print('PASS_ACTUAL_UPDATE_TOTALS_AND_INVALID_BOUNDARY_REJECTION')
