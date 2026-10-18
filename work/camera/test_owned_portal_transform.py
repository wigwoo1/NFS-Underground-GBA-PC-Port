from pathlib import Path
import struct,json
from owned_portal_transform import transform
p=Path('work/camera');raw=(p/'owned-portals.bin').read_bytes();assert len(raw)%344==0
checks=[]
for offset in range(0,len(raw),344):
 magic,refresh,*_=struct.unpack_from('<8I',raw,offset);assert magic==0x3154504e
 m=struct.unpack_from('<12i',raw,offset+168);regs=struct.unpack_from('<16i',raw,offset+280)
 a=transform(*struct.unpack_from('<2i',raw,offset+32),m);b=transform(*struct.unpack_from('<2i',raw,offset+100),m)
 assert a==(regs[5],regs[10]) and b==(regs[6],regs[8]),(a,b,regs)
 checks.append(dict(refresh=refresh,first=a,second=b))
assert checks
r=dict(result='PASS_RAW_PORTAL_CAMERA_TRANSFORM',edges=len(checks),checks=checks,scope='All captured candidate edges, including ones later rejected; horizontal transform only. Near clipping/projection/hierarchy still pending.')
(p/'owned-portal-transform-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
