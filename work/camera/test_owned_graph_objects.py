from pathlib import Path
import struct,json,collections
from owned_graph_packet import GraphPacket
p=Path('work/camera');packets={}
for file in (p/'graph-packets').glob('*.ngp'):
 packet=GraphPacket.decode(file.read_bytes());packets[packet.refresh]=packet
raw=(p/'owned-graph-objects.bin').read_bytes();offset=0;scenes=collections.defaultdict(dict);keys={};object_count=nonempty=merged=0
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x314f474e and h[7] and h[6]==h[5]*168
 sources=raw[offset+32:offset+128];assert sources[:48]==packets[h[1]].context[256:304];assert h[3] not in scenes[h[1]]
 objects={}
 for n in range(h[5]):
  pos=offset+128+n*168;index=struct.unpack_from('<I',raw,pos)[0];assert index not in objects;objects[index]=raw[pos+4:pos+168]
 seen=set();index=h[4]
 while index!=65535:
  assert index in objects and index not in seen;seen.add(index);index=struct.unpack_from('<H',objects[index],2)[0]
 assert seen==objects.keys();scenes[h[1]][h[3]]=h[4];keys[(sources[:48],h[3])]=h[4]
 object_count+=h[5];nonempty+=bool(h[5]);merged+=bool(sources[66]&8);offset+=128+h[6]
for refresh,packet in packets.items():assert scenes[refresh].keys()==packet.validate().keys()
raw=(p/'owned-object-associations.bin').read_bytes();assert len(raw)%400==0
for pos in range(0,len(raw),400):
 h=struct.unpack_from('<8I',raw,pos);assert keys[(raw[pos+352:pos+400],h[3])]==h[4]
r=dict(result='PASS_COMPLETE_GRAPH_OBJECT_ASSOCIATIONS',scenes=len(scenes),descriptors=sum(map(len,scenes.values())),nonempty_lists=nonempty,object_occurrences=object_count,merged_descriptors=merged,original_associations_exact=len(raw)//400,scope='Full reachable descriptor head/list ownership; merged union selection and callback-complete/model asset closure pending.')
(p/'owned-graph-objects.json').write_text(json.dumps(r,indent=2));print(r)
