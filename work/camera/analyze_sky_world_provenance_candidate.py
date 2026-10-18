import sys,json,hashlib
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text())
assert len(manifest['rows'])==48 and not manifest['missed'] and manifest['pending']==0
rows=[];materials=set();transparent=0
for sequence,row in enumerate(manifest['rows']):
 assert row['sequence']==sequence and row['publication'][:3]==[row['epoch'],row['generation'],row['index']]
 assert row['native_result']==1 and row['commit'][:5]==[row['epoch'],row['generation'],row['source_older'],row['source_newer'],row['index']]
 packet=row['world_packets'];path=folder/packet['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==packet['sha256']
 with np.load(path,allow_pickle=False) as a:
  v=a['vertices'];o=a['offsets'];ids=a['texture_ids'];states=a['states'];records=a['texture_records'];rgba=a['texture_rgba'];provenance=a['provenance'];assert provenance.shape==(packet['draws'],4) and provenance.dtype==np.dtype('<u4');assert np.all(np.isin(provenance[:,0],[1,2,3]));assert np.all((provenance[:,3]==0xffffffff)==(provenance[:,0]!=3))
  assert v.shape==(packet['vertices'],10) and np.isfinite(v).all() and states.shape==(packet['draws'],72)
  assert len(ids)==packet['draws'] and len(o)==len(ids)+1 and o[0]==0 and o[-1]==len(v) and np.all(o[1:]>o[:-1]) and np.all((o[1:]-o[:-1])%3==0)
  assert records.shape==(packet['textures'],4) and rgba.dtype==np.uint8 and rgba.size==packet['texture_bytes']
  assert np.all(ids>=1) and np.all(ids<=len(records))
  cursor=0;textures=[]
  for serial,(w,h,offset,size) in enumerate(records,1):
   w,h,offset,size=map(int,(w,h,offset,size));assert w>0 and h>0 and offset==cursor and size==w*h*4 and offset+size<=len(rgba)
   pixels=rgba[offset:offset+size].reshape(h,w,4);alpha=pixels[:,:,3];assert np.all((alpha==0)|(alpha==255))
   digest=hashlib.sha256(pixels.tobytes()).hexdigest();materials.add((w,h,digest));zeros=int(np.count_nonzero(alpha==0));transparent+=zeros
   textures.append(dict(frame_local_id=serial,width=w,height=h,rgba_sha256=digest,transparent_pixels=zeros,draws=[dict(draw=int(d),kind=int(provenance[d,0]),context=int(provenance[d,1]),view_index=int(provenance[d,2]),face=int(provenance[d,3])) for d in np.flatnonzero(ids==serial)]))
   cursor+=size
  assert cursor==len(rgba)
  rows.append(dict(sequence=sequence,index=row['index'],textures=textures))
out=dict(result='PASS_FRAME_BOUND_MATERIAL_AND_EMITTER_PROVENANCE',frames=len(rows),unique_decoded_materials=len(materials),transparent_pixels_across_snapshots=transparent,rows=rows,scope='Recorded kind/context/view/face identifies the source emitter of every submitted draw; context is not assumed a ROM address. Content hashes identify decoded pixels, not original asset identity. Frame-local IDs are never treated as persistent assets. No visibility, scanout or cadence proof.')
(folder/'world-provenance-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
