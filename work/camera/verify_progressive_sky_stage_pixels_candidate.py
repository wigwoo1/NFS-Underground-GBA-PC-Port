import json,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]);rows=json.loads(manifest.read_text())['rows'];assert len(rows)==16
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
checks=[];transitions=[];previous=None
for row in rows:
 assert row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
 assert row['sky_read_begin_ns']<=row['sky_read_end_ns']<=row['full_read_begin_ns']<=row['full_read_end_ns']
 with np.load(row['file']) as data:
  sky=data['sky'].copy();actual=data['actual'].copy();lo=data['lower'][y[:,None],x[None,:]];hi=data['upper'][y[:,None],x[None,:]]
 assert sky.shape==actual.shape==(32,3240,4)
 opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row['phase'])).astype(np.uint8)
 errors=np.any(np.abs(sky.astype(np.int16)-expected.astype(np.int16))>1,axis=2)&opaque
 fullmatch=np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)&opaque
 checks.append(dict(identity=row['identity'],phase=row['phase'],opaque_pixels=int(opaque.sum()),sky_stage_mismatches=int(errors.sum()),completed_scene_matching_pixels=int(fullmatch.sum())))
 if previous:
  prior,oldsky,oldexpected,oldopaque=previous
  assert row['identity'][:2]==prior['identity'][:2] and row['identity'][2]==prior['identity'][2]+1,'Captured interval has an identity gap'
  changes=(np.max(np.abs(expected.astype(np.int16)-oldexpected.astype(np.int16)),axis=2)>2)&opaque&oldopaque
  held=changes&np.all(sky==oldsky,axis=2)
  transitions.append(dict(from_index=prior['identity'][2],to_index=row['identity'][2],expected_strong_changes=int(changes.sum()),unexpected_held_pixels=int(held.sum())))
 previous=row,sky,expected,opaque
out=dict(result='PASS_PRE_WORLD_SKY_PIXEL_ORACLE' if all(c['opaque_pixels']>1000 and c['sky_stage_mismatches']==0 for c in checks) and all(t['expected_strong_changes']>0 and t['unexpected_held_pixels']==0 for t in transitions) else 'FAIL_PRE_WORLD_SKY_PIXEL_ORACLE',manifest=str(manifest),checks=checks,transitions=transitions,scope='All opaque source sky pixels in the 32-row full-width sampled band, before world occlusion, and all 15 adjacent successful completed fullscene commits. Source colors and position equation verified within one UNORM value. No physical scanout, whole sky outside sampled band, original spatial fidelity, or realtime cadence proof; synchronous readbacks perturb timing.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],min(c['opaque_pixels'] for c in checks),'opaque pixels per frame',sum(t['expected_strong_changes'] for t in transitions),'strong changes');assert out['result'].startswith('PASS'),out
