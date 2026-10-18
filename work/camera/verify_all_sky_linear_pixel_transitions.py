"""Check every bounded visible sky transition, excluding <=2-channel rounding ambiguity."""
import json,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]); rows=json.loads(manifest.read_text())['rows']
assert len(rows)==16
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
previous=None; checks=[]; visibility=[]
for row in rows:
 data=np.load(row['file']); actual=data['actual']
 lo=data['lower'][y[:,None],x[None,:]]; hi=data['upper'][y[:,None],x[None,:]]
 assert actual.shape==(32,3240,4) and 0<=row['phase']<=1
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row['phase'])).astype(np.uint8)
 match=np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)&(lo[:,:,3]>127)&(hi[:,:,3]>127)
 assert row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
 visibility.append(dict(identity=row['identity'],matching_pixels=int(match.sum())))
 if previous:
  prior,old_actual,old_expected,old_match=previous
  if row['identity'][:2]==prior['identity'][:2] and row['identity'][2]==prior['identity'][2]+1:
   robust=(np.max(np.abs(expected.astype(np.int16)-old_expected.astype(np.int16)),axis=2)>2)&match&old_match
   changed=np.any(actual!=old_actual,axis=2)
   missing=int((robust&~changed).sum())
   checks.append(dict(from_index=prior['identity'][2],to_index=row['identity'][2],robust_expected_changes=int(robust.sum()),missing_changes=missing))
   # Retain failures for diagnosis; final gate below remains strict.
 previous=row,actual,expected,match
assert checks and sum(c['robust_expected_changes'] for c in checks)>1000
passed=min(v['matching_pixels'] for v in visibility)>1000 and all(c['missing_changes']==0 for c in checks)
out=dict(result='PASS_ALL_BOUNDED_ROBUST_SKY_TRANSITIONS' if passed else 'FAIL_BOUNDED_SKY_VISIBILITY_OR_MOTION',visibility=visibility,manifest=str(manifest.resolve()),checks=checks,scope='All adjacent transitions in 16 retained GPU captures. Independently matched opaque pixels with expected channel delta >2 must change. Occluded/unmatched/rounding-ambiguous pixels excluded explicitly. No complete-run motion, live cadence or scanout qualification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
print(out['result'],len(checks),'transitions',sum(c['robust_expected_changes'] for c in checks),'robust pixel changes')

if not passed:sys.exit(1)

