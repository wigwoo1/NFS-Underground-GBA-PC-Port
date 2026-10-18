import json,copy
from verify_async_handoff_candidate import verify
r=json.load(open('work/camera/prototype-runs/owned-native-1791533725456537300.json'));verify(r)
for mode in ('missing','alive','pending','count','failure'):
 z=copy.deepcopy(r)
 if mode=='missing':del z['background_copy_shutdown']
 elif mode=='alive':z['background_copy_shutdown']['thread_alive']=True
 elif mode=='pending':z['background_copy_shutdown']['pending']=1
 elif mode=='count':z['background_copy_shutdown']['counts']['admitted']+=1
 else:z['background_copy_shutdown']['counts']['failed']=1
 try:verify(z)
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Invalid copy shutdown accepted')
try:verify(json.load(open('work/camera/prototype-runs/owned-native-1791533605131417600.json')))
except KeyError:pass
else:raise AssertionError('First hung run accepted')
print('PASS_ACTUAL_ASYNC_SHUTDOWN_INCOMPLETE_EVIDENCE_REJECTION')
