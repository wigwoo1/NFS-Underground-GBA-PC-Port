import struct,random,json
from pathlib import Path
from owned_motion_pairs import _decode_records
from owned_source_extent_decode_candidate import extents
rng=random.Random(901)
blocks=[bytes([i])*rng.randrange(0,20) for i in range(12)]
g=b''.join(struct.pack('<4I',0x3147534e,k,123,12)+b''.join(struct.pack('<I',len(b))+b for b in blocks) for k in (1,2,3))
def frame(g):return struct.pack('<6I2Q',0x3346474e,3,len(g),0,0,0,2,3*280896)+g
def reference(f):
 s=_decode_records(f,source_keys=False)
 return s['epoch'],s['refresh'],[len(r['blocks'][5]) if r['kind']==3 else 0 for r in s['records']]
checks=0;rejected=0
for geometry in [g[:i] for i in range(len(g)+1)]+[bytes(bytearray(g[:i])+bytes([g[i]^128])+g[i+1:]) for i in range(len(g))]:
 f=frame(geometry);values=[]
 for fn in (reference,extents):
  try:values.append(('ok',fn(f)))
  except ValueError:values.append(('reject',None))
 assert values[0]==values[1],(checks,values)
 rejected+=values[0][0]=='reject';checks+=1
assert extents(frame(g))==reference(frame(g))
out=dict(result='PASS_SOURCE_EXTENT_VALIDATION_PARITY',cases=checks,rejected=rejected,scope='Deterministic all-prefix truncations and one-bit changes in synthetic three-kind source stream; not arbitrary hostile-buffer proof or live performance.')
Path('work/camera/prototype-runs/source-extent-validation-20261009.json').write_text(json.dumps(out,indent=2));print(out)
