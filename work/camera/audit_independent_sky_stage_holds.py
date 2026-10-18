"""Independent sky-stage hold audit: expected motion never gated on actual match."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());previous=None;checks=[]
x=np.clip(np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int),0,239)
for r in m['rows']:
 raw=(folder/r['pixel_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['pixel_sha256']
 actual=np.frombuffer(raw,np.uint8).reshape(64,3240,4)
 y=np.clip(np.floor((np.arange(r['y'],r['y']+64,dtype=np.float32)+.5)*np.float32(2/27)).astype(int),0,159)
 planes=[]
 for slot in range(2):
  raw=(folder/(str(r['sequence'])+'.input'+str(slot)+'.rgba')).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['input'+str(slot)+'_sha256']
  planes.append(np.frombuffer(raw,np.uint8).reshape(160,240,4)[y[:,None],x[None,:]])
 lo,hi=planes;opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
 expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(r['sky_weight'])).astype(np.uint8)
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']] and r['native_result']==1
 if previous is not None:
  p,pe,pa,po=previous
  if p['y']==r['y']:
   assert p['index']+1==r['index'] and (p['epoch'],p['generation'])==(r['epoch'],r['generation'])
   motion=opaque&po&(np.max(np.abs(expected[:,:,:3].astype(np.int16)-pe[:,:,:3].astype(np.int16)),axis=2)>2)
   held=motion&np.all(actual[:,:,:3]==pa[:,:,:3],axis=2)
   checks.append(dict(previous=p['index'],current=r['index'],y=r['y'],expected_motion_pixels=int(motion.sum()),unexpected_held_pixels=int(held.sum())))
 previous=r,expected.copy(),actual.copy(),opaque.copy()
assert len(m['rows'])==48 and len(checks)==42
out=dict(result='PASS_BOUNDED_INDEPENDENT_SKY_HOLDS' if not any(t['unexpected_held_pixels'] for t in checks) else 'FAIL_SKY_HOLDS',transitions=checks,observable_transitions=sum(t['expected_motion_pixels']>0 for t in checks),scope='Independent source opaque mask and >2 UNORM expected motion; no actual-match filtering. Bounded saved sky-stage captures only, no live cadence or physical scanout qualification.')
(folder/'independent-sky-holds.json').write_text(json.dumps(out,indent=2));print(out['result'],out['observable_transitions'],'observable of',len(checks),'held',sum(t['unexpected_held_pixels'] for t in checks));assert out['result'].startswith('PASS')
