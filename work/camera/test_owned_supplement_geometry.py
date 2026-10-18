from pathlib import Path
import struct,json
p=Path('work/camera');raw=(p/'owned-supplement-geometry.bin').read_bytes();supp=(p/'owned-supplements.bin').read_bytes();owners=(p/'owned-wall-owners.bin').read_bytes();offset=0;records=[];matched=0
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x3147534e and h[6] and h[5]==944+h[4]*140
 data=raw[offset+32:offset+32+h[5]];assert len(data)==h[5]
 source_pos=len(records)*460;expected=struct.unpack_from('<6I',supp,source_pos);assert h[1:3]==expected[1:3] and data[160:176]==supp[source_pos+188:source_pos+204]
 assert h[3]==struct.unpack_from('<H',data,160)[0] and h[4]==struct.unpack_from('<H',data,2)[0]
 ring=[data[944+j*140:1012+j*140] for j in range(h[4])]
 hits=0
 for pos in range(0,len(owners),484):
  oh=struct.unpack_from('<16I',owners,pos)
  if oh[1]==h[1] and owners[pos+132:pos+180]==data[:48] and owners[pos+180:pos+228]==data[48:96]:
   assert owners[pos+64:pos+132] in ring;hits+=1
 matched+=hits;records.append(dict(refresh=h[1],descriptor=h[3],vertices=h[4],matching_walls=hits,bytes=h[5]));offset+=32+h[5]
assert len(records)==len(supp)//460==9 and matched>=1
r=dict(result='PASS_OWNED_SUPPLEMENT_GEOMETRY',records=records,matching_original_wall_calls=matched,scope='Raw supplemental rings/offsets/base materials/animation owned; resolved texture payload ownership still pending.')
(p/'owned-supplement-geometry.json').write_text(json.dumps(r,indent=2));print(r['result'],len(records),matched)
