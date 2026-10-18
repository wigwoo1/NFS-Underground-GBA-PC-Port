import json,copy
from pathlib import Path
from owned_source_process_sidecar_candidate import encode,decode
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];identity=(ns['scenes'][0].graph.epoch,ns['scenes'][0].graph.refresh,ns['scenes'][1].graph.refresh)
try:
 payload=encode(owner,identity);cameras,masks=decode(payload,owner.samples,identity);assert cameras==owner.source_cameras
 for a,m in masks.items():assert bytes(m[0])==bytes(owner.source_masks[a][0]) and bytes(m[1])==bytes(owner.source_masks[a][1]) and m[2:]==owner.source_masks[a][2:]
 bad=[]
 x=copy.deepcopy(payload);x['identity']=(identity[0]+1,*identity[1:]);bad.append(x)
 x=copy.deepcopy(payload);x['cameras']=x['cameras'][:-1];bad.append(x)
 x=copy.deepcopy(payload);x['masks']=x['masks']*2;bad.append(x)
 x=copy.deepcopy(payload);a,o,m,n,d=x['masks'][0];x['masks'][0]=(a,o,b'\x02'+m[1:],n,d);bad.append(x)
 x=copy.deepcopy(payload);a,o,m,n,d=x['masks'][0];x['masks'][0]=(a,o,m,n+1,d);bad.append(x)
 x=copy.deepcopy(payload);a,o,m,n,d=x['masks'][0];raw=bytearray(o);import struct
 offset_values=list(struct.unpack('<'+'I'*(len(o)//4),o));offset_values[1]+=1;raw=struct.pack('<'+'I'*len(offset_values),*offset_values);x['masks'][0]=(a,raw,m,n,d);bad.append(x)
 for x in bad:
  try:decode(x,owner.samples,identity)
  except ValueError:pass
  else:raise AssertionError('Invalid sidecar accepted')
 snapshots={a:(bytes(v[0]),bytes(v[1]),v[2],dict(v[3])) for a,v in masks.items()}
 owner.close()
 assert all((bytes(v[0]),bytes(v[1]),v[2],v[3])==snapshots[a] for a,v in masks.items())
 result=dict(private_buffers_after_owner_close=True,result='PASS',exact_samples=len(masks),malformed_rejections=len(bad),identity=identity,scope='Actual owned eight source masks/cameras roundtrip and bounded malformed rejection; sidecar component, no child service/live integration.')
finally:owner.close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-process-sidecar-20261007');cp.mkdir(exist_ok=True);(cp/'result.json').write_text(json.dumps(result,indent=2))
for name in ('owned_source_process_sidecar_candidate.py','test_source_process_sidecar.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print(result)

