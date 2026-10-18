"""Versioned immutable raw graph/material transport. Objects remain a separate dependency."""
from dataclasses import dataclass
import struct,zlib
MAGIC=0x314b474e
@dataclass(frozen=True)
class GraphPacket:
 refresh:int
 root:int
 context:bytes
 geometry:bytes
 offsets:bytes
 materials:bytes
 def __post_init__(self):
  for field in ('context','geometry','offsets','materials'):object.__setattr__(self,field,bytes(getattr(self,field)))
 def encode(self):
  blocks=tuple(bytes(x) for x in (self.context,self.geometry,self.offsets,self.materials));payload=b''.join(blocks)
  return struct.pack('<9I',MAGIC,1,self.refresh,self.root,*map(len,blocks),zlib.crc32(payload))+payload
 def graph(self):
  cursor=0;graph={};required=set();links=set();vertices_total=0
  top,bottom=struct.unpack_from('<2H',self.context,92)
  while cursor<len(self.geometry):
   if cursor+64>len(self.geometry):raise ValueError('Truncated descriptor')
   index,n,_,_=struct.unpack_from('<4I',self.geometry,cursor);desc=self.geometry[cursor+16:cursor+64];cursor+=64
   if index in graph or not 0<n<=32 or cursor+n*68>len(self.geometry):raise ValueError('Invalid descriptor ring')
   ring=self.geometry[cursor:cursor+n*68];cursor+=n*68;vertices_total+=n
   if struct.unpack_from('<H',desc,2)[0]!=n:raise ValueError('Descriptor count mismatch')
   required.update((struct.unpack_from('<H',desc,4)[0],struct.unpack_from('<H',desc,8)[0]))
   for j in range(n):
    required.add(struct.unpack_from('<H',ring,j*68+44)[0]);links.add(struct.unpack_from('<H',ring,j*68+48)[0])
   graph[index]=(ring,top,bottom)
  if self.root not in graph or (links-{65535})-graph.keys():raise ValueError('Incomplete portal graph')
  if len(self.offsets)!=vertices_total*32:raise ValueError('Incomplete vertex offsets')
  return graph,required-{65535}
 def validate(self):
  if len(self.context)!=896:raise ValueError('Invalid scene context')
  graph,required=self.graph();cursor=0;seen=set();textures={}
  while cursor<len(self.materials):
   if cursor+120>len(self.materials):raise ValueError('Truncated material')
   h=struct.unpack_from('<12I',self.materials,cursor);cursor+=120
   if h[0]!=0x314d474e or h[1]!=self.refresh or h[3] in seen:raise ValueError('Invalid material identity')
   seen.add(h[3]);mode=h[9]
   if mode==1:
    if not 0<h[8]<=0x80000 or cursor+h[8]>len(self.materials):raise ValueError('Truncated texture')
    textures[h[10]]=(h[7],h[8]);cursor+=h[8]
   elif mode==2:
    if textures.get(h[10])!=(h[7],h[8]):raise ValueError('Missing shared texture')
   elif mode!=3 or h[8]:raise ValueError('Unresolved material')
  if seen!=required:raise ValueError('Incomplete material ownership')
  return graph
 @classmethod
 def decode(cls,raw):
  raw=bytes(raw)
  if len(raw)<36:raise ValueError('Truncated graph packet')
  h=struct.unpack_from('<9I',raw)
  if h[:2]!=(MAGIC,1) or sum(h[4:8])+36!=len(raw) or len(raw)>32*1024*1024:raise ValueError('Invalid graph packet header')
  if zlib.crc32(raw[36:])!=h[8]:raise ValueError('Corrupt graph packet')
  cursor=36;blocks=[]
  for n in h[4:8]:blocks.append(raw[cursor:cursor+n]);cursor+=n
  packet=cls(h[2],h[3],*blocks);packet.validate();return packet
