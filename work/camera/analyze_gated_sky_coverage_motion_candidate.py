import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and not m['pending']
observations={item['prepare']:item['stats'] for item in m['gate_observations']}
assert set(observations)=={119,120,167,168,169}
assert observations[119]==[0,0,0]
assert observations[120][0]==observations[167][0]==1 and observations[167][1]>observations[120][1]>0
assert observations[168][0]==observations[169][0]==0
assert observations[168][1]==observations[169][1]==observations[167][1]
assert m['writes_and_hashes_after_shutdown'] and m['payload_files']==288 and m['payload_bytes']<=m['payload_limit']==160*1024*1024
rows=[];transitions=[];prior={}
def read(r):
 data=(folder/r['pixel_file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==r['pixel_sha256']
 return np.frombuffer(data,np.uint8).reshape(64,3240,4)
for r in m['rows']:
 assert r['backend']=='owned-d3d-gated-sky-coverage-transaction-candidate.dll' and r['native_result']==1
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['coverage_begin_ns']<=r['coverage_end_ns']<=r['commit'][6]<=r['coverage_poll_begin_ns']<=r['coverage_poll_end_ns']
 assert r['coverage_poll_thread']==r['thread']
 data=(folder/r['coverage_file']).read_bytes();assert len(data)==3240*64 and hashlib.sha256(data).hexdigest()==r['coverage_sha256']
 visible=np.frombuffer(data,np.uint8).reshape(64,3240)==255
 stage=read(r);final=read(r['final_capture'])
 assert not np.any(visible & np.any(stage!=final,axis=2)),'Coverage-marked pixels changed after sky'
 rows.append(dict(index=r['index'],y=r['y'],visible_sky_pixels=int(visible.sum())))
 if r['y'] in prior:
  old,old_stage,old_final,old_visible=prior[r['y']]
  assert r['index']==old['index']+1 and (r['epoch'],r['generation'])==(old['epoch'],old['generation'])
  eligible=visible & old_visible & (np.max(np.abs(stage[:,:,:3].astype(np.int16)-old_stage[:,:,:3].astype(np.int16)),axis=2)>2)
  held=eligible & np.all(final==old_final,axis=2)
  transitions.append(dict(index=r['index'],y=r['y'],eligible_moving_sky_pixels=int(eligible.sum()),held_visible_sky_pixels=int(held.sum())))
 prior[r['y']]=r,stage,final,visible
out=dict(result='ANALYZED_LIVE_CONSERVATIVE_SKY_COVERAGE',rows=rows,transitions=transitions,total_visible_sky_pixels=sum(r['visible_sky_pixels'] for r in rows),observable_transitions=sum(r['eligible_moving_sky_pixels']>0 for r in transitions),held_visible_sky_pixels=sum(r['held_visible_sky_pixels'] for r in transitions),scope='Coverage eligibility independent of RGB agreement; marked pixels required exactly unchanged by later passes. Bounded heavily instrumented GPU diagnostic; no original-speed/scanout60 qualification. Live mask color baseline parity remains unverified.')
(folder/'coverage-motion-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','transitions')})

