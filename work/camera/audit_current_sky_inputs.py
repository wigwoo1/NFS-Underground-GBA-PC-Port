import json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);m=json.loads((p/'manifest.json').read_text());checks=[];motions=[];previous=None
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
band_y=m['rows'][0].get('band_y',648);band_height=m['rows'][0].get('band_height',16)
y=np.floor((np.arange(band_y,band_y+band_height,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
for i,r in enumerate(m['rows']):
 assert r['sky_status']==0 and r['sky_enabled']==[1,1]
 actual=np.frombuffer((p/r['file']).read_bytes(),np.uint8).reshape(band_height,3840,4)[:,300:3540]
 planes=[np.frombuffer((p/(str(i)+'.input'+str(s)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4) for s in range(2)]
 lo,hi=[a[y[:,None],x[None,:]] for a in planes]
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(r['sky_weights'][1])).astype(np.uint8)
 opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
 match=opaque&np.all(np.abs(actual[:,:,:3].astype(np.int16)-expected[:,:,:3].astype(np.int16))<=1,axis=2)
 checks.append(dict(draw=r['draw_number'],fraction=r['sky_weights'][1],matching_pixels=int(match.sum()),opaque_pixels=int(opaque.sum())))
 if previous is not None:
  old_expected,old_match,old_actual=previous
  moving=np.any(expected[:,:,:3]!=old_expected[:,:,:3],axis=2)&match&old_match
  motions.append(dict(draw=r['draw_number'],matching_reference_motion=int(moving.sum()),actual_motion_at_matches=int((moving&np.any(actual[:,:,:3]!=old_actual[:,:,:3],axis=2)).sum())))
 previous=expected.copy(),match.copy(),actual.copy()
out=dict(samples=len(checks),checks=checks,motions=motions,moving_reference_transitions=sum(a['matching_reference_motion']>0 for a in motions),scope='Current backend final colors match independently blended source planes within 1 UNORM. Coincident foreground colors remain possible; no successful commit binding, full-scene cadence or scanout proof.')
(p/'source-reference-audit.json').write_text(json.dumps(out,indent=2))
print(dict(samples=len(checks),minimum_matching_pixels=min(a['matching_pixels'] for a in checks),moving_reference_transitions=out['moving_reference_transitions']))


