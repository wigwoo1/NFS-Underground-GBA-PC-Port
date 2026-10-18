import json,sys,hashlib
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and not m['pending']
x=np.floor((np.arange(3240,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27)).astype(int)
rows=[];previous={};transitions=[]
for r in m['rows']:
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 planes=[]
 for n in range(2):
  data=(folder/(str(r['sequence'])+'.input'+str(n)+'.rgba')).read_bytes();assert hashlib.sha256(data).hexdigest()==r['input'+str(n)+'_sha256'];planes.append(np.frombuffer(data,np.uint8).reshape(160,240,4))
 data=(folder/r['pixel_file']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['pixel_sha256'];actual=np.frombuffer(data,np.uint8).reshape(64,3240,4)
 y=np.floor((r['y']+np.arange(64,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27)).astype(int)
 lower,upper=[p[y[:,None],x[None,:]] for p in planes]
 opaque=(lower[:,:,3]>127)&(upper[:,:,3]>127)
 phase=np.float32(r['sky_weight']);assert 0<=phase<=1
 expected=np.rint(lower.astype(np.float32)+(upper.astype(np.float32)-lower.astype(np.float32))*phase).clip(0,255).astype(np.uint8)
 error=np.max(np.abs(actual.astype(np.int16)-expected.astype(np.int16)),axis=2)
 assert np.any(opaque) and not np.any(opaque & (error>1)), 'Captured opaque sky differs from independent blend oracle'
 rows.append(dict(index=r['index'],y=r['y'],opaque_pixels=int(opaque.sum()),max_error=int(error[opaque].max()),sampled_equal_endpoints=int(np.count_nonzero(opaque & np.all(lower==upper,axis=2)))))
 if r['y'] in previous:
  old,oe,oa,oo=previous[r['y']];assert old['index']+1==r['index']
  eligible=opaque & oo
  transitions.append(dict(index=r['index'],y=r['y'],oracle_changed_pixels=int(np.count_nonzero(eligible & np.any(expected!=oe,axis=2))),actual_changed_pixels=int(np.count_nonzero(eligible & np.any(actual!=oa,axis=2)))))
 previous[r['y']]=r,expected,actual,opaque
out=dict(result='PASS_CAPTURED_OPAQUE_SKY_BLEND_ORACLE',rows=rows,transitions=transitions,scope='Independent NumPy float32 blend and source-coordinate sampling from exact captured planes; opaque domain within1UNORM. Transparent/discard domain excluded explicitly; finite earlier capture, not sustained60 or original-fidelity certification.')
(folder/'sky-blend-oracle.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(result=out['result'],frames=len(rows),held_band_rows=[r for r in rows if r['y']==1440],held_band_transitions=[t for t in transitions if t['y']==1440])))
