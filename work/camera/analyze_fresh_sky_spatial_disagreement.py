import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
folder=Path(sys.argv[1]); rows=json.loads((folder/'manifest.json').read_text())['rows']
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
checks=[];worst=None
for row in rows:
 d=np.load(row['file']);actual=d['actual'];lo=d['lower'][y[:,None],x[None,:]];hi=d['upper'][y[:,None],x[None,:]]
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row['phase'])).astype(np.uint8)
 opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
 error=np.max(np.abs(actual.astype(np.int16)-expected.astype(np.int16)),axis=2)
 match=(error<=1)&opaque
 item=dict(identity=row['identity'],phase=row['phase'],opaque=int(opaque.sum()),matching=int(match.sum()),mismatching_opaque=int((opaque&~match).sum()),rows=[dict(source_y=int(yy),opaque=int(opaque[k].sum()),matching=int(match[k].sum())) for k,yy in enumerate(y)])
 checks.append(item)
 if worst is None or item['matching']<worst[0]:worst=(item['matching'],actual,expected,opaque,match,item)
_,actual,expected,opaque,match,item=worst
panel=np.zeros_like(actual);panel[:,:,:3]=np.where(match[:,:,None],np.array([0,255,0]),np.where(opaque[:,:,None],np.array([255,0,0]),np.array([40,40,40])))[:,:,:3];panel[:,:,3]=255
image=np.concatenate([actual,expected,panel],axis=0)
out=Path(sys.argv[2]);out.mkdir(exist_ok=True)
Image.fromarray(image).resize((1080,288)).save(out/'worst-sky-actual-expected-mask.png')
(out/'spatial-disagreement.json').write_text(json.dumps(dict(result='DIAGNOSTIC_ONLY',checks=checks,worst_identity=item['identity'],scope='Top actual, middle expected, bottom green matching/red unmatched opaque/gray source transparent. Spatial mismatch alone cannot establish occlusion versus fidelity disagreement.'),indent=2))
print(json.dumps({k:item[k] for k in ('identity','phase','opaque','matching','mismatching_opaque')}))
