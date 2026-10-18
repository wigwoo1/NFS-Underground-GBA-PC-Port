import json,sys,hashlib
from pathlib import Path
import numpy as np
src=Path(sys.argv[1]);r=json.loads(src.read_text());rows=r['rows'];assert len(rows)==16
transitions=[];prior=None
for row in rows:
 assert row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
 assert len(row['full_rgba_sha256'])==64
 with np.load(row['file']) as z:scene=z['scene'].copy()
 assert scene.shape==(270,480,4)
 if prior:
  old,im=prior
  assert row['identity'][:2]==old['identity'][:2] and row['identity'][2]==old['identity'][2]+1
  d=np.max(np.abs(scene[:,:,:3].astype(np.int16)-im[:,:,:3].astype(np.int16)),axis=2)>2
  cells=[]
  for ya,yb in ((0,90),(90,180),(180,270)):
   for xa,xb in ((38,173),(173,308),(308,442)):
    cells.append(dict(sample_bounds=[xa,ya,xb,yb],changed_pixels=int(d[ya:yb,xa:xb].sum()),sampled_pixels=(yb-ya)*(xb-xa)))
  transitions.append(dict(older=old['identity'],newer=row['identity'],alpha_from=old['alpha'],alpha_to=row['alpha'],pair_changed=(old['older'],old['newer'])!=(row['older'],row['newer']),full_frame_changed=old['full_rgba_sha256']!=row['full_rgba_sha256'],cells=cells))
 prior=row,scene
assert len(transitions)==15
out=dict(result='BOUNDED_FULLSCENE_MOTION_MEASURED',source=str(src.resolve()),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),transitions=transitions,full_frame_holds=sum(not t['full_frame_changed'] for t in transitions),cell_moving_transition_counts=[sum(t['cells'][i]['changed_pixels']>0 for t in transitions) for i in range(9)],scope='16 consecutive successful native commits; exact whole RGBA hashes and fixed stride8 pixel samples in9 viewport regions. No layer attribution, geometry matching, original fidelity or scanout certification. Readback and compression perturb timing, so diagnostic cannot qualify60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='transitions'})
