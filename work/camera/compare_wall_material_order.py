"""Audit native order and wall UV endpoints against recovered command data."""
from pathlib import Path
import json,struct
p=Path('outputs/nfsug-native-renderer/camera-research')
audit=json.loads((p/'native-wall-invocation-audit.json').read_text())
world=json.loads((p/'native-world-audit.json').read_text())
b=Path('work/camera/prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-native-scene.bin').read_bytes()
tag,offset,size=struct.unpack_from('<III',b,32+2*12);assert tag==3
magic,count=struct.unpack_from('<II',b,offset);assert magic==0x314f464e and size==8+count*4
order=struct.unpack_from('<'+'I'*count,b,offset+8)
native=[]
for index in order:
 if index==0xffffffff:native.append([3,0]);continue
 assert index<len(world['surfaces'])
 s=world['surfaces'][index];native.append([s['kind'],int(s['source'],16)])
original=[[c[0],0 if c[0]==3 else c[2]] for c in audit['original_dispatch']]
assert native==original, 'Native source command order differs from retained original dispatch'
materials=[]
for region in audit['suspect_regions']:
 if region['pose']!='sampled':continue
 for edge in region['edges']:
  s=next(s for s in world['surfaces'] if s['source']==edge['source'])
  width,height=s['texture_size'];raw=bytes.fromhex(edge['scratch_hex']);u0,u1,t0,b0,t1,b1=struct.unpack_from('<6i',raw,16)
  recovered=[[u0/(128*width),t0/(128*height)],[u1/(128*width),t1/(128*height)],[u1/(128*width),b1/(128*height)],[u0/(128*width),b0/(128*height)]]
  error=max(abs(a-b) for pair,ref in zip(s['uv'],recovered) for a,b in zip(pair,ref))
  assert error==0, (s['source'],error)
  materials.append(dict(source=s['source'],native_uv=s['uv'],original_prepared_uv=recovered,max_endpoint_error=error,metadata_mode=s['metadata_mode'],writer_state_counts=s['wall_state_counts']))
assert len(materials)==5
report=dict(result='PASS',original_order=original,native_order=native,exact_order_match=original==native,materials=materials,scope='Exact captured source command order and prepared UV endpoint comparison; does not verify column texel addressing, writer coverage or whole-scene image fidelity.')
(p/'native-wall-material-order-comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
