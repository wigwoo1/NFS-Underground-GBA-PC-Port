"""Independent CPU reconstruction of actual sky shader sampling on opaque coverage."""
import json,sys,numpy as np
from pathlib import Path
f=Path(sys.argv[1]);m=json.loads((f/'manifest.json').read_text());rows=[]
x=(np.arange(3840,dtype=np.float32)+np.float32(.5)-np.float32(300))*np.float32(2)/np.float32(27)
y=(np.arange(600,616,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27)
tx=np.clip(np.floor(x).astype(int),0,239);ty=np.clip(np.floor(y).astype(int),0,159)
for r in m['rows']:
 prefix=r['plane_prefix'];planes=[np.frombuffer((f/(prefix+'.plane'+str(i)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4) for i in range(2)]
 low=planes[0][ty[:,None],tx[None,:]];high=planes[1][ty[:,None],tx[None,:]]
 shifted=np.floor(x+np.float32(r['source_weights'][1]))>np.floor(x)
 expected=np.where((shifted[None,:] & (high[:,:,3]>127))[:,:,None],high,low)
 coverage=(np.arange(3840)[None,:]>=300)&(np.arange(3840)[None,:]<3540)&(expected[:,:,3]>127)
 actual=np.frombuffer((f/r['sky_stage_file']).read_bytes(),np.uint8).reshape(16,3840,4)
 mismatched=int(np.any(actual[:,:,:3]!=expected[:,:,:3],axis=2)[coverage].sum())
 rows.append(dict(index=r['index'],covered_pixels=int(coverage.sum()),mismatched_pixels=mismatched,phase=r['source_weights'][1]))
out=dict(samples=len(rows),rows=rows,mismatched_pixels=sum(r['mismatched_pixels'] for r in rows),scope='CPUshader source-coordinate/floor/fractionalshift reconstruction versus actualsky-stage RGB onopaqueinviewportcoverage. Excludestransparentbackdrop/outsideviewport. Notoriginalgamefidelity/scanout/cadence.')
(f/'expected-phase-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});assert len(rows)==32 and all(r['covered_pixels']>0 for r in rows) and out['mismatched_pixels']==0
