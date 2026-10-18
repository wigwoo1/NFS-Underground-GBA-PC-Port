"""Original ordered spatial descriptor selection over owned graph sources."""
import math,struct
from owned_root_offset_queries import signed32
class SpatialDescriptors:
 def __init__(self,graph):
  self.rows={};at=offset=0
  while at<len(graph.geometry):
   key,n,_,_=struct.unpack_from('<4I',graph.geometry,at);desc=graph.geometry[at+16:at+64];at+=64;ring=graph.geometry[at:at+n*68];at+=n*68
   self.rows[key]=(desc,ring,graph.offsets[offset:offset+n*32]);offset+=n*32
 def row(self,key):
  if key not in self.rows:raise ValueError('Missing owned spatial descriptor')
  return self.rows[key]
 def contains(self,key,point):
  if len(point)!=2 or not all(math.isfinite(x) for x in point):raise ValueError('Invalid spatial query')
  _,ring,_=self.row(key);n=len(ring)//68;x,z=point;integer=x==int(x) and z==int(z)
  for i in range(n):
   ax,az=struct.unpack_from('<2i',ring,((i-1)%n)*68);bx,bz=struct.unpack_from('<2i',ring,i*68)
   cross=(bz-az)*(x-ax)-(z-az)*(bx-ax)
   if integer:cross=signed32(int(cross))
   elif not -2147483648<=cross<=2147483647:raise ValueError('Unverified fractional spatial cross wrap')
   if cross<0:return False
  return True
 def neighbors(self,key):
  _,ring,offsets=self.row(key)
  for i in range(len(ring)//68):
   material,flags=struct.unpack_from('<H',ring,i*68+42)[0],struct.unpack_from('<H',ring,i*68+46)[0]
   if material!=65535:flags=struct.unpack_from('<H',offsets,i*32+14)[0]
   target=struct.unpack_from('<H',ring,i*68+50)[0]
   if target!=65535 and not flags&0x1000:yield target
 def linked(self,key):
  desc,_,_=self.row(key);link=struct.unpack_from('<H',desc,32)[0]
  result=link if not struct.unpack_from('<H',desc,8)[0] and link!=65535 else key
  self.row(result);return result
 def select(self,current,point):
  if self.contains(current,point):return current
  for target in self.neighbors(current):
   if self.contains(target,point):return self.linked(target)
  return 65535
 def fallback(self,current,point):
  for first in self.neighbors(current):
   for second in self.neighbors(first):
    if self.contains(second,point):return self.linked(second)
  return 65535
 def pair_root(self,current,queries):
  plus,minus=queries;forward=self.select(current,(plus[0],plus[2]))
  if forward==65535:forward=self.fallback(current,(plus[0],plus[2]))
  if forward==65535:forward=current
  backward=self.select(current,(minus[0],minus[2]));desc,_,_=self.row(forward);redirect=struct.unpack_from('<H',desc,34)[0]
  root=forward if redirect==65535 else redirect;self.row(root)
  return root,(forward,backward)
