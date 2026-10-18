from pathlib import Path
import struct,json
from owned_supplemental_region import walk
p=Path('work/camera');raw=(p/'owned-object-chains.bin').read_bytes();offset=0;calls=0;selected=[];objects_total=0
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x3148434e and h[7]==1 and h[6]==h[5]*168
 parent=struct.unpack_from('<8H',raw,offset+32);objects={};start=offset+304
 for i in range(h[5]):
  pos=start+i*168;index=struct.unpack_from('<I',raw,pos)[0];assert index not in objects;objects[index]=raw[pos+4:pos+168]
 for index,value in walk(h[3],objects,parent[1:5]):selected.append((h[1],objects[index],value))
 objects_total+=len(objects);calls+=1;offset=start+h[6]
expected=[];raw=(p/'owned-supplements.bin').read_bytes()
for pos in range(0,len(raw),460):
 h=struct.unpack_from('<6I',raw,pos);expected.append((h[1],raw[pos+24:pos+188],struct.unpack_from('<8H',raw,pos+188)))
assert selected==expected,(len(selected),len(expected))
for head,objects in [(1,{}),(1,{1:bytes(164)})]:
 try:walk(head,objects,(2,238,0,158))
 except ValueError:pass
 else:raise AssertionError('Invalid ownership accepted')
r=dict(result='PASS_OWNED_OBJECT_CHAINS',calls=calls,owned_objects=objects_total,supplements=len(selected),exact_order=True,scope='Component source selection; live integration and independent region head recovery remain pending.')
(p/'owned-object-chains.json').write_text(json.dumps(r,indent=2));print(r)
