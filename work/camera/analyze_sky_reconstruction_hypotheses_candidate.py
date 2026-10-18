import json
from pathlib import Path
import numpy as np
folder=Path('work/camera/prototype-runs/async-skybands-1791589780164939700');m=json.loads((folder/'manifest.json').read_text());totals={k:0 for k in ('lower','upper','linear','anchored','discrete')};rows=[]
u=(np.arange(3240)+.5)*2/27;x=np.floor(u).astype(int);edge=(np.floor(u)+1)*13.5;centers=np.arange(3240)+.5;support=np.minimum(1,edge-centers)
for r in m['rows']:
 i=r['sequence'];final=np.frombuffer((folder/r['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);y=np.floor((np.arange(r['y'],r['y']+64)+.5)*2/27).astype(int)
 planes=[np.frombuffer((folder/(str(i)+'.input'+str(j)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4)[y[:,None],x[None,:]] for j in range(2)];lo,hi=planes;phase=np.float32(r['sky_weight']);coverage=np.clip((phase*13.5-(edge-centers-support))/support,0,1);shift=np.floor(u+phase)>np.floor(u)
 choices={'lower':lo,'upper':hi,'linear':np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*phase).astype(np.uint8),'anchored':np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*coverage[None,:,None]).astype(np.uint8),'discrete':np.where(shift[None,:,None],hi,lo)}
 counts={}
 for name,expected in choices.items():
  valid=(lo[:,:,3]>127)&(hi[:,:,3]>127)
  counts[name]=int((valid&np.all(np.abs(final[:,:,:3].astype(np.int16)-expected[:,:,:3].astype(np.int16))<=1,axis=2)).sum());totals[name]+=counts[name]
 rows.append(dict(sequence=i,y=r['y'],phase=float(phase),matches=counts))
out=dict(result='LIVE_SKY_RECONSTRUCTION_HYPOTHESIS_MEASUREMENT',totals=totals,rows=rows,scope='Same opaque intersection for allhypotheses; finalpixels maybeoccluded, nofitusedtoalterrenderer orsourcegeometry. Diagnosis only.')
(folder/'hypothesis-audit.json').write_text(json.dumps(out,indent=2));print(totals)
