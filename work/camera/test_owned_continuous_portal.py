from pathlib import Path
import struct,json
from owned_portal_transform import transform
from owned_portal_continuous import edge
p=Path('work/camera');raw=(p/'owned-projected-portals.bin').read_bytes();rb=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(rb)//4)+'I',rb);checks=[]
for o in range(0,len(raw),368):
 m=struct.unpack_from('<12i',raw,o+168);fb=raw[o+216:o+280];a=transform(*struct.unpack_from('<2i',raw,o+32),m);b=transform(*struct.unpack_from('<2i',raw,o+100),m);expected=struct.unpack_from('<6i',raw,o+344)
 result=edge(a,b,struct.unpack_from('<i',fb,16)[0],struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0],table,bool(expected[5]));assert result==expected[:5]
 checks.append(dict(near_flags=result[2]))
r=dict(result='PASS_CONTINUOUS_PORTAL_INTEGER_LATTICE',edges=len(checks),scope='Continuous arithmetic matches original at all107captured integer inputs; fractional near-plane topology and sampled pose limits require separate audit.')
(p/'owned-continuous-portal-tests.json').write_text(json.dumps(r,indent=2));print(r)
