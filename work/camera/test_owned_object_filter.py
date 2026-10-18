from pathlib import Path
import struct,json
from owned_object_filter import depth_distance,signed,ordered
p=Path('work/camera');raw=(p/'owned-object-filter.bin').read_bytes();assert raw and len(raw)%244==0
front=behind=0
for pos in range(0,len(raw),244):
 h=struct.unpack_from('<8I',raw,pos);assert h[0]==0x31464f4e
 actual=depth_distance(raw[pos+32:pos+196],raw[pos+196:pos+244]);expected=(signed(h[4]),signed(h[5]),signed(h[6]));assert actual==expected,(pos,actual,expected)
 if actual[0]>0:front+=1
 else:behind+=1
assert ordered([(1,1,5),(2,1,10),(3,1,5),(4,0,100),(5,1,7)])==[2,5,3,1]
r=dict(result='PASS_OWNED_OBJECT_DEPTH_DISTANCE',records=len(raw)//244,front=front,behind=behind,ordering_ties=True,scope='Exact projection and ordering component; callback eligibility/visited state and full source-list integration pending.')
(p/'owned-object-filter.json').write_text(json.dumps(r,indent=2));print(r)
