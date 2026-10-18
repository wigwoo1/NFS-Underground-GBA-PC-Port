"""Read-only sparse memory from one complete raw graph snapshot and immutable ROM."""
import struct
class ClosedSceneMemory:
 def __init__(self,closed,rom):
  self.rom=bytes(rom);self.owned={};self.missing=[];g=closed.graph;state=g.context[:256]
  def word(at):return struct.unpack_from('<I',state,at)[0]
  def add(address,data):
   for i,value in enumerate(data):
    if address+i in self.owned and self.owned[address+i]!=value:raise ValueError('Conflicting owned scene memory')
    self.owned[address+i]=value
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
 def read(self,address,size):
  if size<0 or size>0x100000 or address+size>0x100000000:raise ValueError('Invalid scene read')
  if all(address+i in self.owned for i in range(size)):return bytes(self.owned[address+i] for i in range(size))
  offset=address-0x08000000
  if 0<=offset and offset+size<=len(self.rom):
   return bytes(self.owned.get(address+i,self.rom[offset+i]) for i in range(size))
  self.missing.append((address,size));raise ValueError('Unowned scene read')
