import json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);m=json.loads((p/'manifest.json').read_text());rows=[]
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
for i,r in enumerate(m['rows']):
 y=np.floor((np.arange(r['band_y'],r['band_y']+r['band_height'],dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
 actual=np.frombuffer((p/r['file']).read_bytes(),np.uint8).reshape(r['band_height'],3840,4)[:,300:3540,:3].astype(np.int16)
 planes=[np.frombuffer((p/(str(i)+'.input'+str(s)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4)[y[:,None],x[None,:]] for s in range(2)]
 lower,upper=planes;opaque=(lower[:,:,3]>127)&(upper[:,:,3]>127)
 expected=np.rint(lower[:,:,:3].astype(float)+(upper[:,:,:3].astype(float)-lower[:,:,:3].astype(float))*np.float32(r['sky_weights'][1])).astype(np.int16)
 def match(v):return opaque&np.all(np.abs(actual-v.astype(np.int16))<=1,axis=2)
 lo,hi,blend=match(lower[:,:,:3]),match(upper[:,:,:3]),match(expected)
 rows.append(dict(draw=r['draw_number'],fraction=r['sky_weights'][1],lower_matches=int(lo.sum()),upper_matches=int(hi.sum()),blend_matches=int(blend.sum()),endpoint_only=int(((lo|hi)&~blend).sum())))
out=dict(rows=rows,scope='Same-coordinate endpoint and fractional RGB comparisons with verified viewport offset; foreground coincidence possible, no stage ownership or scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
print({k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in ['lower_matches','upper_matches','blend_matches','endpoint_only']})
