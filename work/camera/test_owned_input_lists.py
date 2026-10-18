from pathlib import Path
import struct,json,collections
from owned_object_filter import select_owned
p=Path('work/camera');callbacks=collections.defaultdict(dict);raw=(p/'owned-object-eligibility.bin').read_bytes()
for pos in range(0,len(raw),244):
 h=struct.unpack_from('<8I',raw,pos)
 if h[2]==0x03002090:
  source=raw[pos+32:pos+196];callbacks[h[7]][struct.unpack_from('<H',source)[0]]=source
raw=(p/'owned-object-input-lists.bin').read_bytes();offset=0;selected={};calls=objects_total=0
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x31494f4e and h[7] and h[6]==h[5]*168
 camera=raw[offset+32:offset+80];objects={}
 for n in range(h[5]):
  pos=offset+80+n*168;index=struct.unpack_from('<I',raw,pos)[0];assert index not in objects;objects[index]=raw[pos+4:pos+168]
 selected[h[4]]=select_owned(h[3],objects,camera,callbacks[h[4]])
 objects_total+=len(objects);calls+=1;offset+=80+h[6]
raw=(p/'owned-object-chains.bin').read_bytes();offset=region=0
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);indices=[struct.unpack_from('<I',raw,offset+304+n*168)[0] for n in range(h[5])]
 assert selected.get(region,[])==indices,(region,selected.get(region),indices)
 offset+=304+h[6];region+=1
r=dict(result='PASS_RAW_ASSOCIATION_LIST_SELECTION',lists=calls,objects=objects_total,region_chains_exact=region,scope='Raw association lists and callback-complete sources reproduce sampled chains; complete live scene integration and merged coverage pending.')
(p/'owned-object-input-lists.json').write_text(json.dumps(r,indent=2));print(r)
