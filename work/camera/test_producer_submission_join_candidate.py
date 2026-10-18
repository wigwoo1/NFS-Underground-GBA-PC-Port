import json,copy
from analyze_producer_submission_join_candidate import joined
r=json.load(open('work/camera/prototype-runs/owned-native-1791532581242626800.json'));assert joined(r)['count']>0
for mode in ('identity','bounds','native','drop'):
 z=copy.deepcopy(r);s=z['producer_retention']['long_scene_preparations'];w=s['records'][0]['worker_submission']
 if mode=='identity':w['scene_identity'][1]+=1
 elif mode=='bounds':w['submit_end_ns']=s['records'][0]['completed_ns']+1
 elif mode=='native':w['native_copy_unlocked_ns']=w['native_push_internal_ns']+100
 else:s['dropped']=1
 try:joined(z)
 except AssertionError:pass
 else:raise AssertionError('Invalid '+mode+' evidence accepted')
print('PASS_ACTUAL_COMPLETE_JOIN_AND_INVALID_IDENTITY_BUDGET_REJECTION')
