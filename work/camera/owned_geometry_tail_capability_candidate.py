"""Isolated parent-owned tail capability; not installed in live transport."""
import struct
from owned_segmented_frame_candidate import SegmentedFrame
class GeometryTailOwners:
 def __init__(self,generation,owners):
  if type(generation)is not int or generation<0 or type(owners)is not tuple or not 1<=len(owners)<=2 or any(type(x)is not bytes for x in owners):raise ValueError('Invalid tail capability registration')
  if sum(map(len,owners))>32*1024*1024:raise ValueError('Tail owner budget exceeded')
  headers=[]
  for owner in owners:
   if len(owner)<40 or len(owner)>16*1024*1024:raise ValueError('Invalid tail owner extent')
   h=struct.unpack_from('<6I2Q',owner)
   if h[0]!=0x3346474e or not h[6] or h[7]!=h[1]*280896 or 40+sum(h[2:6])!=len(owner):raise ValueError('Invalid tail owner envelope')
   headers.append(h)
  if len({h[6] for h in headers})!=1:raise ValueError('Mixed tail owner epochs')
  self.generation=generation;self.owners=owners;self.headers=tuple(headers)
 def _owner(self,generation,key):
  if self.owners is None or type(generation)is not int or generation!=self.generation or type(key)is not int or not 0<=key<len(self.owners):raise ValueError('Unknown or retired tail capability')
  return self.owners[key],self.headers[key]
 def geometry(self,generation,key):
  owner,original=self._owner(generation,key);h=list(original);h[3:6]=[0,0,0]
  return b''.join((struct.pack('<6I2Q',*h),memoryview(owner)[40:40+h[2]]))
 def restore(self,generation,key,prefix):
  owner,original=self._owner(generation,key)
  if type(prefix)is not bytes or not 40<=len(prefix)<=16*1024*1024:raise ValueError('Invalid geometry prefix')
  h=list(struct.unpack_from('<6I2Q',prefix))
  if h[0]!=original[0] or h[1]!=original[1] or tuple(h[6:])!=original[6:] or h[3:6]!=[0,0,0] or len(prefix)!=40+h[2]:raise ValueError('Unpaired geometry tail capability')
  h[3:6]=original[3:6];full_prefix=b''.join((struct.pack('<6I2Q',*h),memoryview(prefix)[40:]))
  return SegmentedFrame(full_prefix,owner,40+original[2])
 def close(self):self.owners=None;self.headers=()
