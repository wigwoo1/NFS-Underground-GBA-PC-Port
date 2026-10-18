"""Immutable diagnostic scene bundle; model assets/live publication remain pending."""
from dataclasses import dataclass
import struct,zlib
from owned_graph_packet import GraphPacket
FIELDS=('graph','objects','callbacks','supplements','textures','associations','graph_objects')
def chunks(raw,kind):
 cursor=0
 while cursor<len(raw):
  if cursor+32>len(raw):raise ValueError('Truncated scene section')
  h=struct.unpack_from('<8I',raw,cursor)
  size=128+h[6] if kind=='graph_objects' else 400 if kind=='associations' else 80+h[6] if kind=='objects' else 244 if kind=='callbacks' else 32+h[5] if kind=='supplements' else 120+struct.unpack_from('<I',raw,cursor+40)[0]
  if size<32 or cursor+size>len(raw):raise ValueError('Truncated scene record')
  yield h,raw[cursor:cursor+size]
  cursor+=size
@dataclass(frozen=True)
class SceneBundle:
 graph:bytes
 objects:bytes
 callbacks:bytes
 supplements:bytes
 textures:bytes
 associations:bytes
 graph_objects:bytes
 def __post_init__(self):
  for field in FIELDS:object.__setattr__(self,field,bytes(getattr(self,field)))
 def validate(self):
  graph=GraphPacket.decode(self.graph);camera=graph.context[256:304];regions=set();supplements={};associations={};lists={}
  for h,raw in chunks(self.associations,'associations'):
   if h[0]!=0x3241534e or raw[352:400]!=camera or h[7] in associations:raise ValueError('Invalid scene association')
   associations[h[7]]=(h,raw)
  if not associations:raise ValueError('Missing region associations')
  graph_heads={}
  for h,raw in chunks(self.graph_objects,'graph_objects'):
   if h[0]!=0x314f474e or not h[7] or raw[32:80]!=camera or h[3] in graph_heads or h[6]!=h[5]*168:raise ValueError('Invalid graph object ownership')
   objects={}
   for j in range(h[5]):
    index=struct.unpack_from('<I',raw,128+j*168)[0]
    if index in objects:raise ValueError('Duplicate graph object')
    objects[index]=raw[132+j*168:296+j*168]
   index=h[4];seen=set()
   while index!=65535:
    if index not in objects or index in seen:raise ValueError('Incomplete graph object chain')
    seen.add(index);index=struct.unpack_from('<H',objects[index],2)[0]
   if seen!=objects.keys():raise ValueError('Unreachable graph object')
   graph_heads[h[3]]=h[4]
  if graph_heads.keys()!=graph.validate().keys():raise ValueError('Missing invisible-region associations')
  for h,raw in associations.values():
   if graph_heads.get(h[3])!=h[4]:raise ValueError('Inconsistent region association')
  for h,raw in chunks(self.objects,'objects'):
   if h[0]!=0x31494f4e or not h[7] or raw[32:80]!=camera or h[6]!=h[5]*168:raise ValueError('Invalid owned object list')
   regions.add(h[4]);lists[h[4]]=h[3]
  for index,(h,raw) in associations.items():
   if raw[66]&8:raise ValueError('Merged association ownership pending')
   if h[4]==65535:
    if index in lists:raise ValueError('Unexpected object list')
   elif lists.get(index)!=h[4]:raise ValueError('Missing region object list')
  if regions-associations.keys():raise ValueError('Missing object association')
  for h,raw in chunks(self.callbacks,'callbacks'):
   if h[0]!=0x31454f4e or h[7] not in regions or raw[196:244]!=camera:raise ValueError('Mixed callback scene')
  for h,raw in chunks(self.supplements,'supplements'):
   key=(h[1],h[2],h[3])
   if h[0]!=0x3147534e or not h[6] or raw[80:128]!=camera or h[5]!=944+h[4]*140 or key in supplements:raise ValueError('Mixed supplemental scene')
   supplements[key]=h[4]
  edges=set()
  for _,raw in chunks(self.textures,'textures'):
   h=struct.unpack_from('<12I',raw);key=(h[1],h[2],h[3]);edge=(*key,h[4])
   if h[0]!=0x3154534e or not h[11] or key not in supplements or h[4]>=supplements[key] or edge in edges:raise ValueError('Incomplete supplemental texture')
   edges.add(edge)
  if len(edges)!=sum(supplements.values()):raise ValueError('Missing supplemental textures')
  return graph
 def encode(self):
  payload=b''.join(getattr(self,f) for f in FIELDS)
  return struct.pack('<10I',0x3142534e,3,*(len(getattr(self,f)) for f in FIELDS),zlib.crc32(payload))+payload
 @classmethod
 def decode(cls,raw):
  raw=bytes(raw)
  if len(raw)<40:raise ValueError('Truncated scene bundle')
  h=struct.unpack_from('<10I',raw)
  if h[:2]!=(0x3142534e,3) or sum(h[2:9])+40!=len(raw) or len(raw)>32*1024*1024 or zlib.crc32(raw[40:])!=h[9]:raise ValueError('Invalid scene bundle')
  cursor=40;blocks=[]
  for n in h[2:9]:blocks.append(raw[cursor:cursor+n]);cursor+=n
  bundle=cls(*blocks);bundle.validate();return bundle
