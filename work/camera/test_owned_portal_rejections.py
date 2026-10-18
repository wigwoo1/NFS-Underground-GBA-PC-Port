from pathlib import Path
import struct,json,collections
from owned_portal_transform import transform,project_edge
p=Path('work/camera');raw=(p/'owned-portals.bin').read_bytes();projected=(p/'owned-projected-portals.bin').read_bytes()
assert len(raw)%344==0 and len(projected)%368==0
ids={struct.unpack_from('<I',projected,o+28)[0] for o in range(0,len(projected),368)}
rb=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(rb)//4)+'I',rb);checks=[];reasons=collections.Counter()
for offset in range(0,len(raw),344):
 index=struct.unpack_from('<I',raw,offset+28)[0];m=struct.unpack_from('<12i',raw,offset+168);fb=raw[offset+216:offset+280]
 a=transform(*struct.unpack_from('<2i',raw,offset+32),m);b=transform(*struct.unpack_from('<2i',raw,offset+100),m);near=struct.unpack_from('<i',fb,16)[0]
 result=project_edge(a,b,near,struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0],table)
 assert (result is not None)==(index in ids),(index,a,b,result,index in ids)
 reason='projected' if result is not None else 'far' if max(a[1],b[1])>0x6000 else 'both_behind_near'
 reasons[reason]+=1;checks.append(dict(index=index,reason=reason))
assert len(checks)==121
r=dict(result='PASS_COMPLETE_CAPTURED_PORTAL_REJECTIONS',candidates=len(checks),counts=dict(reasons),checks=checks,scope='All121captured candidates in selected racing interval; far branch may have no actual coverage, hierarchy still pending.')
(p/'owned-portal-rejection-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],r['counts'])
