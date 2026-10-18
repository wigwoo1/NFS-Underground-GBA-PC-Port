from pathlib import Path
import struct,json
from owned_portal_transform import transform,project_edge
p=Path('work/camera');raw=(p/'owned-projected-portals.bin').read_bytes();assert len(raw)%368==0
rb=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(rb)//4)+'I',rb);checks=[]
for offset in range(0,len(raw),368):
 m=struct.unpack_from('<12i',raw,offset+168);fb=raw[offset+216:offset+280];a=transform(*struct.unpack_from('<2i',raw,offset+32),m);b=transform(*struct.unpack_from('<2i',raw,offset+100),m)
 expected=struct.unpack_from('<6i',raw,offset+344)
 result=project_edge(a,b,struct.unpack_from('<i',fb,16)[0],struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0],table,bool(expected[5]))
 assert result==expected[:5],(result,expected,a,b)
 checks.append(dict(refresh=struct.unpack_from('<I',raw,offset+4)[0],near_flags=result[2]))
assert checks
r=dict(result='PASS_RAW_PORTAL_PROJECTION',edges=len(checks),checks=checks,scope='Captured edges reaching projection; rejected branches not yet comprehensively audited, hierarchy still pending.')
(p/'owned-portal-projection-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
