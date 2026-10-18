from pathlib import Path
import struct,json,collections
from owned_object_filter import eligibility,depth_distance,ordered
p=Path('work/camera');raw=(p/'owned-object-eligibility.bin').read_bytes();assert raw and len(raw)%244==0
records=[]
for pos in range(0,len(raw),244):
 h=struct.unpack_from('<8I',raw,pos);assert h[0]==0x31454f4e
 records.append((h,raw[pos+32:pos+196],raw[pos+196:pos+244]))
counts=collections.Counter();projected=[];changed=0;by_region=collections.defaultdict(list)
for n,(h,source,camera) in enumerate(records):
 if h[2]!=0x03002044:continue
 decision=eligibility(source,bool(h[5]));counts[decision]+=1
 has_post=n+1<len(records) and records[n+1][0][2]==0x03002090
 assert has_post==(decision in ('callback','project','hidden')),(n,decision,has_post)
 if has_post:
  post,new,new_camera=records[n+1];assert post[1]==h[1] and post[4]==h[4]
  changed+=new!=source
  if struct.unpack_from('<H',new,8)[0]&4:
   projected.append((post[1],post[4],new,new_camera))
   depth,distance,_=depth_distance(new,new_camera);by_region[post[7]].append((struct.unpack_from('<H',new)[0],depth,distance))
reference=(p/'owned-object-filter.bin').read_bytes();expected=[]
for pos in range(0,len(reference),244):
 h=struct.unpack_from('<8I',reference,pos);expected.append((h[1],h[3],reference[pos+32:pos+196],reference[pos+196:pos+244]))
# The original projection stores distance at+40 between post and reference.
assert len(projected)==len(expected)
for a,b in zip(projected,expected):
 assert a[:2]==b[:2] and a[3]==b[3] and a[2][:40]==b[2][:40] and a[2][44:]==b[2][44:]
chain_raw=(p/'owned-object-chains.bin').read_bytes();offset=0;region_id=0
while offset<len(chain_raw):
 h=struct.unpack_from('<8I',chain_raw,offset);expected_order=[struct.unpack_from('<I',chain_raw,offset+304+i*168)[0] for i in range(h[5])]
 assert ordered(by_region[region_id])==expected_order,(region_id,ordered(by_region[region_id]),expected_order)
 offset+=304+h[6];region_id+=1
r=dict(region_chains_exact=region_id,result='PASS_OWNED_OBJECT_ELIGIBILITY',prechecks=sum(counts.values()),decisions=dict(counts),projected=len(projected),callback_source_changes=changed,scope='Observed eligibility exact; callbacks remain original simulation responsibility, merged coverage absent.')
(p/'owned-object-eligibility.json').write_text(json.dumps(r,indent=2));print(r)
