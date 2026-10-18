import json,copy
from pathlib import Path
from verify_pause_native_segment_coverage import verify
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791642956527214800.json').read_text());out=verify(r);assert not out['cadence_screen_passed'] and out['segments'][-1]['initial_active_hold_ms']==37.3218
cases=[]
for name in ['dropped','zero_success','outside_active','skipped','reset','pause_order']:
 bad=copy.deepcopy(r);s=bad['live_observation_stats']['whole_run_api_intervals']['native_success_segments'];rows=s['records']
 if name=='dropped':s['dropped']=1
 elif name=='zero_success':rows.pop();s['total']-=1
 elif name=='outside_active':rows[1]['first_success_ns']=bad['pause_events'][0]['begin_ns']
 elif name=='skipped':rows[1]['last_index']+=1
 elif name=='reset':rows[1]['epoch']+=1
 else:bad['pause_events'][0]['native_resume_ack_ns']=bad['pause_events'][0]['begin_ns']-1
 try:verify(bad)
 except ValueError:cases.append(name)
 else:raise AssertionError(name+' accepted')
assert len(cases)==6
result=dict(result='PASS_PAUSE_NATIVE_COVERAGE_GUARDS',rejections=cases,scope='Actual pause capture with malformed/dropped/reset/zero-success evidence must not qualify; no performance change.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/pause-native-coverage-guards.json').write_text(json.dumps(result,indent=2));print(result)
