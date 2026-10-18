import json,copy
from owned_producer_long_scene_candidate import ProducerRows
from analyze_long_scene_preparation_candidate import analyze
r=json.load(open('work/camera/prototype-runs/owned-native-1791532314646348500.json'));q=ProducerRows()
for x in r['producer_cycle_samples']:q.append(x)
r['producer_retention']=q.stats();r['timing']['producer_read_validate_reconstruct_submit']['count']=q.total_records
out=analyze(r);assert out['count']==q.long_total
for mode in ('drop','gc','count'):
 z=copy.deepcopy(r)
 if mode=='drop':z['producer_retention']['long_scene_preparations']['dropped']=1
 elif mode=='gc':z['gc_trace_dropped']=1
 else:z['producer_retention']['long_scene_preparations']['total']+=1
 try:analyze(z)
 except AssertionError:pass
 else:raise AssertionError('Invalid evidence accepted')
print('PASS_ACTUAL_SCENE_ROWS_AND_INCOMPLETE_LEDGER_REJECTION')
