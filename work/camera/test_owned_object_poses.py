from pathlib import Path
import struct,json
from owned_motion_pairs import records
p=Path('work/camera');references=[]
for file in (p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'):
 frame=records(file.read_bytes());camera=next(bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in frame['records'] if r['kind'] in (1,2))
 for r in frame['records']:
  if r['kind']==3:references.append((frame['refresh'],camera,bytes(r['blocks'][2])))
raw=(p/'owned-object-poses.bin').read_bytes();checks=[]
assert len(raw)%292==0
for offset in range(0,len(raw),292):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x31504f4e and h[7]
 camera=raw[offset+196:offset+244];pose=raw[offset+244:offset+292]
 matches=[f for f,c,m in references if c==camera and m==pose];assert len(matches)==1,(h,matches)
 checks.append(dict(capture=h[1],frame=matches[0],skin=h[4]))
assert len(checks)==7
r=dict(result='PASS_OWNED_OBJECT_MATRIX_PARITY',matrices_exact=7,checks=checks,scope='Original skin-selected composed matrices exact; pose table closure and live scene integration pending.')
(p/'owned-object-poses.json').write_text(json.dumps(r,indent=2));print(r)
