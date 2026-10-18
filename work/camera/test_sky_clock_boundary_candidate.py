import json
from pathlib import Path
from owned_sky_motion_totals_candidate import SkyMotionTotals
from owned_present_interval_totals_candidate import PresentationIntervalTotals
sky=SkyMotionTotals();api=PresentationIntervalTotals()
for index,(committed,returned) in enumerate([(0,10),(25000001,25000009)]):
 row=dict(native_result=1,sky_source_angles=[0,0],alpha=.5,sky_fraction=0,epoch=2,generation=1,display_index=index,native_committed_sample=[0]*6+[committed],callback_timing=dict(present_begin_ns=committed+1,present_end_ns=returned),transaction_end_ns=returned+1)
 sky.observe(row);api.observe(row)
s=sky.stats();a=api.stats();assert s['commit_intervals_over_25ms']==1 and s['api_intervals_over_25ms']==0 and a['over_25ms']==0
assert s['adjacent_transitions']==a['adjacent_successful_intervals']==1
out=dict(result='PASS_DISTINCT_COMMIT_AND_API_THRESHOLD_CLOCKS',native_commit_over25=1,api_over25=0,scope='Synthetic 25ms threshold-crossing diagnostic counter guard; no live sky motion claim.')
Path('work/camera/prototype-runs/sky-clock-boundary-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
