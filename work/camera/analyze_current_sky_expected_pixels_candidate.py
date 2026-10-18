import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==32 and m['pending']==0
previous=None;rows=[];transitions=[]
x=np.arange(3840,dtype=np.float32)+np.float32(.5);source=(x-np.float32(300))*np.float32(2)/np.float32(27);tx=np.clip(np.floor(source).astype(int),0,239)
y=np.arange(648,664,dtype=np.float32)+np.float32(.5);ty=np.clip(np.floor(y*np.float32(2)/np.float32(27)).astype(int),0,159)
for index,r in enumerate(m['rows']):
 assert r['backend']=='owned-d3d-current-sky-input-candidate.dll' and r['strip_y']==648 and r['strip_height']==16
 assert r['native_result']==1 and r['present']['status']==0 and r['present']['thread']==r['thread']
 assert r['publication'][:3]==[r['epoch'],r['generation'],r['index']] and r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['read_begin_ns']<=r['read_end_ns']<=r['present']['completed_ns']<=r['commit'][6]
 data=(folder/r['strip_file']).read_bytes();assert len(data)==3840*16*4 and hashlib.sha256(data).hexdigest()==r['strip_sha256']
 final=np.frombuffer(data,np.uint8).reshape(16,3840,4)
 planes=[np.frombuffer((folder/(str(index)+'.input'+str(slot)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4) for slot in range(2)]
 lo=planes[0][ty[:,None],tx[None,:]];hi=planes[1][ty[:,None],tx[None,:]]
 shifted=np.floor(source+np.float32(r['sky_weight']))>np.floor(source)
 expected=np.where((shifted[None,:]&(hi[:,:,3]>127))[:,:,None],hi,lo)
 opaque=(expected[:,:,3]>127)&(x[None,:]>=300)&(x[None,:]<3540)
 matches=opaque&np.all(final[:,:,:3]==expected[:,:,:3],axis=2)
 rows.append(dict(index=r['index'],opaque_reference_pixels=int(opaque.sum()),matching_final_pixels=int(matches.sum())))
 if previous is not None:
  old,old_expected,old_match=previous
  moving=np.any(expected[:,:,:3]!=old_expected[:,:,:3],axis=2)
  survivors=moving&matches&old_match
  transitions.append(dict(previous=old['index'],current=r['index'],same_source_pair=(old['source_older'],old['source_newer'])==(r['source_older'],r['source_newer']),expected_changed_pixels=int(moving.sum()),matching_final_changed_pixels=int(survivors.sum())))
 previous=r,expected.copy(),matches.copy()
assert any(t['matching_final_changed_pixels']>0 and t['same_source_pair'] for t in transitions)
out=dict(result='PASS_CURRENT_SKY_EXPECTED_FINAL_COLOR_MOTION',samples=len(rows),rows=rows,transitions=transitions,moving_reference_transitions=sum(t['expected_changed_pixels']>0 for t in transitions),matching_final_motion_transitions=sum(t['matching_final_changed_pixels']>0 for t in transitions),scope='CPU shader-coordinate reference from actual cached input planes; same-coordinate final RGB matches expected sky RGB in both frames. Does not establish exclusive foreground provenance, all-sky coverage, physical scanout or60fps; readback perturbs timing.')
(folder/'expected-final-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','transitions')})
