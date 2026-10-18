"""Audit bounded live pixels and native commits; does not certify cadence."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());rows=m['rows'];assert len(rows)==32
transitions=[];previous=None
for r in rows:
 key=[r['epoch'],r['generation'],r['index']]
 assert r['publication'][:3]==key and r['native_result']==1
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['present']['status']==0 and r['present']['thread']==r['thread']
 assert r['read_begin_ns']<=r['read_end_ns']<=r['present']['completed_ns']<=r['commit'][6]
 assert 0<=r['sky_weight']<=1 and 0<=r['alpha']<=1
 data=(folder/r['strip_file']).read_bytes();assert len(data)==3840*64*4 and hashlib.sha256(data).hexdigest()==r['strip_sha256']
 pixels=np.frombuffer(data,np.uint8).reshape(64,3840,4)[:,:,:3]
 if previous:
  a,old=previous;assert r['index']>a['index']
  changes=int(np.count_nonzero(np.any(pixels!=old,axis=2)))
  sky_changed=(r['sky_weight'],r['sky_lower_sha256'],r['sky_upper_sha256'])!=(a['sky_weight'],a['sky_lower_sha256'],a['sky_upper_sha256'])
  transitions.append(dict(index=r['index'],changed_strip_pixels=changes,sky_input_changed=sky_changed,same_scene_pair=(a['source_older'],a['source_newer'])==(r['source_older'],r['source_newer']),commit_gap_ms=(r['commit'][6]-a['commit'][6])/1e6))
 previous=(r,pixels.copy())
out=dict(result='PASS_LIVE_4K_PIXEL_COMMIT_BINDING',rows=len(rows),transitions=transitions,changed_strip_transitions=sum(x['changed_strip_pixels']>0 for x in transitions),sky_changed_transitions=sum(x['sky_input_changed'] for x in transitions),scope='Actual pending 4K rendering followed by matching native presentation commit. Captured strip may contain world/HUD overlap; differences cannot exclusively establish sky movement. Full-frame readback perturbs timing; no 60fps or scanout proof.')
(folder/'audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='transitions'}))
