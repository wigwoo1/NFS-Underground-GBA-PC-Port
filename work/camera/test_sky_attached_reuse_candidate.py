"""Exact sky attachment outputs/errors and immutable-owner identity reuse."""
import time,statistics,json
from pathlib import Path
from owned_sky_frame import attach_sky as baseline
from owned_sky_attached_reuse_candidate import attach_sky as candidate
source=Path('work/camera/test_owned_sky_frame.py').read_text().split('cp=Path(')[0]
exec(compile(source,'sky_fixture','exec'))
checks=[]
for label,value in [('original',original),('attached',result),('mutable',bytearray(result)),('view',memoryview(result))]+[(f'invalid-{i}',bytes(v)) for i,v in enumerate(cases)]:
 outputs=[]
 for api in (baseline,candidate):
  try:outputs.append(('ok',api(value,scene)))
  except ValueError as e:outputs.append(('error',str(e)))
 assert outputs[0]==outputs[1],label
 checks.append(dict(case=label,outcome=outputs[0][0]))
assert candidate(result,scene) is result
assert type(candidate(bytearray(result),scene)) is bytes
rows=[]
for name,api in [('baseline',baseline),('candidate',candidate)]:
 durations=[]
 for i in range(120):
  start=time.perf_counter_ns();v=api(result,scene);end=time.perf_counter_ns();assert v==result
  if i>=20:durations.append((end-start)/1e6)
 rows.append(dict(path=name,median_ms=statistics.median(durations),max_ms=max(durations)))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-sky-attachment-live-20261008')
r=dict(result='PASS',checks=checks,timing=rows,frame_bytes=len(result),immutable_identity_reused=True,scope='Archived actual owned-sky fixture; exact outputs/errors and mutable-copy ownership; component timings only, not live4K or cadence proof.')
(cp/'already-attached-reuse.json').write_text(json.dumps(r,indent=2));print(r)
