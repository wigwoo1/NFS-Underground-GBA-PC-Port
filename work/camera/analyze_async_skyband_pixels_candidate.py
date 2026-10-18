import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
rows=[];transitions=[];previous=None
source=(np.arange(3240,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27);tx=np.clip(np.floor(source).astype(int),0,239)
for i,r in enumerate(m['rows']):
 assert r['sequence']==i and r['capture_id']==120+i and r['backend']=='owned-d3d-async-skyband-candidate.dll'
 assert r['publication'][:3]==[r['epoch'],r['generation'],r['index']] and r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['native_result']==1 and r['present']['status']==0 and r['thread']==r['present']['thread']==r['poll_thread']
 assert r['capture_begin_ns']<=r['capture_end_ns']<=r['present']['completed_ns']<=r['commit'][6]<=r['poll_begin_ns']<=r['poll_end_ns']
 data=(folder/r['pixel_file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==r['pixel_sha256'];final=np.frombuffer(data,np.uint8).reshape(64,3240,4)
 planes=[]
 for slot in range(2):
  data=(folder/(str(i)+'.input'+str(slot)+'.rgba')).read_bytes();assert len(data)==240*160*4 and hashlib.sha256(data).hexdigest()==r['input'+str(slot)+'_sha256'];planes.append(np.frombuffer(data,np.uint8).reshape(160,240,4))
 ty=np.clip(np.floor((np.arange(r['y'],r['y']+64,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27)).astype(int),0,159)
 lo=planes[0][ty[:,None],tx[None,:]];hi=planes[1][ty[:,None],tx[None,:]];shifted=np.floor(source+np.float32(r['sky_weight']))>np.floor(source)
 expected=np.where((shifted[None,:]&(hi[:,:,3]>127))[:,:,None],hi,lo);opaque=expected[:,:,3]>127;match=opaque&np.all(final[:,:,:3]==expected[:,:,:3],axis=2)
 rows.append(dict(index=r['index'],y=r['y'],opaque_reference_pixels=int(opaque.sum()),matching_final_pixels=int(match.sum()),capture_enqueue_ms=(r['capture_end_ns']-r['capture_begin_ns'])/1e6,poll_ms=(r['poll_end_ns']-r['poll_begin_ns'])/1e6))
 if previous is not None:
  a,old_expected,old_match,old_final,old_opaque=previous
  if a['y']==r['y']:
   assert a['index']+1==r['index'] and (a['epoch'],a['generation'])==(r['epoch'],r['generation'])
   moving=opaque&old_opaque&np.any(expected[:,:,:3]!=old_expected[:,:,:3],axis=2);survive=moving&match&old_match
   transitions.append(dict(y=r['y'],previous=a['index'],current=r['index'],expected_changed_pixels=int(moving.sum()),matching_final_changed_pixels=int(survive.sum()),actual_final_changed_pixels=int(np.any(final[:,:,:3]!=old_final[:,:,:3],axis=2).sum())))
 previous=r,expected.copy(),match.copy(),final.copy(),opaque.copy()
assert len(transitions)==42
out=dict(result='PASS_ASYNC_SKYBAND_BINDING_REFERENCE_MEASUREMENT',samples=len(rows),transitions=transitions,rows=rows,not_ready=m['not_ready'],moving_reference_transitions=sum(t['expected_changed_pixels']>0 for t in transitions),matching_final_motion_transitions=sum(t['matching_final_changed_pixels']>0 for t in transitions),scope='6bands x8frames, exact nonblocking capture/source/nativecommit binding. CPU shader-coordinate reference matches final RGB; coincident foreground colors possible. Not exclusive sky ownership, all-frame/scanout/smooth60 proof; instrumentation perturbs timing.')
(folder/'audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','transitions')})
