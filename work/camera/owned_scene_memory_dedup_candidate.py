"""Read-only sparse memory from one complete raw graph snapshot and immutable ROM."""
import struct
from bisect import bisect_left,bisect_right
from types import MappingProxyType
class ClosedSceneMemory:
 def __init__(self,closed,rom):
  self.rom=bytes(rom);self._ranges=[];starts=[];self.missing=[];g=closed.graph;state=g.context[:256]
  seen={}
  def word(at):return struct.unpack_from('<I',state,at)[0]
  def add(address,data):
   data=bytes(data)
   if not data:return
   if seen.get(address)==data:return
   end=address+len(data);index=max(0,bisect_right(starts,address)-1)
   while index<len(self._ranges) and self._ranges[index][0]<end:
    old_address,old=self._ranges[index];lo=max(address,old_address);hi=min(end,old_address+len(old))
    if lo<hi and data[lo-address:hi-address]!=old[lo-old_address:hi-old_address]:raise ValueError('Conflicting owned scene memory')
    if old_address<=address and end<=old_address+len(old):seen[address]=data;return
    index+=1
   index=bisect_left(starts,address);starts.insert(index,address);self._ranges.insert(index,(address,data));seen[address]=data
  add(word(84),g.context[256:304]);add(word(80),g.context[304:368])
  at=offset=0
  while at<len(g.geometry):
   identifier,n,descriptor,vertices=struct.unpack_from('<4I',g.geometry,at);add(descriptor,g.geometry[at+16:at+64]);at+=64;ring=g.geometry[at:at+n*68];add(vertices,ring);at+=n*68
   for i in range(n):
    oi=struct.unpack_from('<H',ring,i*68+42)[0]
    if oi!=65535:add(word(24)+oi*32,g.offsets[offset+i*32:offset+(i+1)*32])
   offset+=n*32
  at=0
  while at<len(g.materials):
   h=struct.unpack_from('<12I',g.materials,at);body=g.materials[at+48:at+120];base=word(32)+h[3]*32;phase=struct.unpack_from('<H',body,34)[0];add(base,body[:32]);add(word(72)+struct.unpack_from('<H',body)[0]*8,body[32:40]);add(base+phase*32,body[40:72]);at+=120+(h[8] if h[9]==1 else 0)
  if g.faces:
   from owned_face_dependencies import decode_faces
   for address,data in decode_faces(g.faces,g).items():add(address,data)
  merged=[]
  for address,data in self._ranges:
   if merged and address<=merged[-1][0]+len(merged[-1][1]):
    old_address,old=merged[-1];skip=old_address+len(old)-address
    old.extend(data[max(0,skip):])
   else:merged.append((address,bytearray(data)))
  self._ranges=tuple((a,bytes(d)) for a,d in merged);self._starts=tuple(a for a,_ in merged);self.owned_byte_count=sum(len(d) for _,d in merged)
 @property
 def owned(self):return MappingProxyType({a+i:v for a,d in self._ranges for i,v in enumerate(d)})
 @property
 def _owned_addresses(self):return tuple(a+i for a,d in self._ranges for i in range(len(d)))
 def read(self,address,size):
  if size<0 or size>0x100000 or address+size>0x100000000:raise ValueError('Invalid scene read')
  if size==0:return b''
  end=address+size;index=max(0,bisect_right(self._starts,address)-1);offset=address-0x08000000
  # Merged ranges are disjoint: a contained read is already the exact overlay.
  if index<len(self._ranges):
   start,data=self._ranges[index]
   if start<=address and end<=start+len(data):return data[address-start:end-start]
  rom_backed=0<=offset and offset+size<=len(self.rom)
  result=bytearray(self.rom[offset:offset+size]) if rom_backed else bytearray(size);covered=address
  while index<len(self._ranges):
   start,data=self._ranges[index]
   if start>=end:break
   lo=max(address,start);hi=min(end,start+len(data))
   if lo<hi:
    if not rom_backed and lo>covered:break
    result[lo-address:hi-address]=data[lo-start:hi-start];covered=max(covered,hi)
   index+=1
  if rom_backed or covered==end:return bytes(result)
  self.missing.append((address,size));raise ValueError('Unowned scene read')

# A bounded per-thread cache lets road and model preparation share an exact
# immutable publication. Different ROM/scene objects always rebuild.
import threading
_scene_memory_local=threading.local()
def scene_memory(closed,rom):
 entries=getattr(_scene_memory_local,'entries',[])
 for owner,source,memory in entries:
  if owner is closed and source is rom:return memory
 memory=ClosedSceneMemory(closed,rom)
 entries.append((closed,rom,memory));_scene_memory_local.entries=entries[-4:]
 return memory
