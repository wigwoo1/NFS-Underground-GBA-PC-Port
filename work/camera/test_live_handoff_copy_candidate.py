import json,copy
from analyze_live_handoff_copy_candidate import analyze
r=json.load(open('work/camera/prototype-runs/owned-native-1791532849952528300.json'));assert analyze(r)['count']>0
for mode in ('negative','budget','missing'):
 z=copy.deepcopy(r);w=z['producer_retention']['long_scene_preparations']['records'][0]['worker_submission']
 if mode=='negative':w['handoff_allocate_ns']=-1
 elif mode=='budget':w['handoff_memcpy_ns']=w['native_copy_unlocked_ns']+1000
 else:del w['handoff_allocate_ns']
 try:analyze(z)
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Invalid copy profile accepted')
print('PASS_ACTUAL_LIVE_HANDOFF_COPY_BUDGET_REJECTION')
