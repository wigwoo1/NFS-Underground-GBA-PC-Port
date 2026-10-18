from owned_motion_clock import deadline,scene_samples,REFRESH,HZ
from pathlib import Path
import json
refs=[8758,8762,8766,8769,8773,8776,8780];samples=[]
for a,b in zip(refs,refs[1:]):
 s=scene_samples(123,refs[0],a,b)
 assert all(0<=x['alpha']<1 for x in s);samples+=s
assert all(b['index']==a['index']+1 for a,b in zip(samples,samples[1:]))
assert deadline(123,60*3600)==123+3600*1000000000
assert set(deadline(0,i+1)-deadline(0,i) for i in range(600))=={16666666,16666667}
assert REFRESH*60!=HZ,'Original logic clock must not be forced to60Hz'
r=dict(result='PASS_ORIGINAL_CYCLE_60HZ_PRESENTATION_GRID',presentation_slots=len(samples),one_hour_no_rounding_drift=True,original_cycle_ratio_preserved=True,scope='Clock arithmetic only; scheduling/GPU completion/gameplay cadence unverified.')
Path('work/camera/owned-motion-clock-tests.json').write_text(json.dumps(r,indent=2));print(r)
