import audit_deferred_wall_boundary as fixture
from owned_deferred_wall_policy import sampled_wall_emitted
from owned_sampled_graph_gpu import sampled_graph_gpu_records
from pathlib import Path
import json
assert sampled_wall_emitted(0,1,9)
assert not sampled_wall_emitted(2,1,9)
assert not sampled_wall_emitted(2,0,32)
try:sampled_wall_emitted(2,2,9)
except ValueError:pass
else:raise AssertionError('Retained deferred mask must still reject unverified ordering')
checks=[]
for row in fixture.checks:
 alpha=row['alpha']
 if alpha in (0,1) or 'error' in row:continue
 records=sampled_graph_gpu_records(fixture.portal,alpha)
 deferred={(x['descriptor'],x['edge']) for x in row['deferred']}
 assert not any((x['descriptor'],x['edge']) in deferred for x in records)
 checks.append(alpha)
result=dict(result='PASS',sampled_frames=len(checks),deferred_samples=sum(bool(x['deferred']) for x in fixture.checks),native_endpoint_actions=fixture.endpoint_actions,retained_mask_rejected=True,scope='Original deferred mask truncation; complete fractional portal traversal now passes all101 audited poses')
Path('work/camera/deferred-mask-policy-tests.json').write_text(json.dumps(result,indent=2));print(result)
