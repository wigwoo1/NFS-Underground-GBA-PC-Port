import json
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791422124322488700.json').read_text());rows={x['display_index']:x for x in r['presentation_samples'] if x.get('interpolated')};out=[]
for index in (841,1023):
 x=rows[index];q=x['queued_stage_timing'];st=x['native_commit_stage_ns'];out.append(dict(display=index,queued_ready_ms=(q[4]-q[3])/1e6,ready_poll_total_ms=q[5]/1e6,ready_poll_max_ms=q[6]/1e6,ready_yield_ms=q[7]/1e6,wait=x['native_wait_timing'],commit_stages=st,deadline=x['presentation_deadline_ns'],present_begin=x['present_begin_ns'],draw_complete=x['draw_complete_ns'],queued_observations=x['queued_fence_observations']))
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-queued-minute-20261007/remaining-gaps.json');p.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
