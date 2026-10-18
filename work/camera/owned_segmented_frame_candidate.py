"""Private geometry with an immutable retained HUD/background/text owner.
Experimental representation; contiguous GPU ABI integration is pending.
"""
from dataclasses import dataclass
import struct
@dataclass(frozen=True)
class SegmentedFrame:
 prefix: bytes
 base: bytes
 tail_offset: int
 def __post_init__(self):
  if type(self.prefix) is not bytes or type(self.base) is not bytes:raise ValueError('Immutable owners required')
  if len(self.prefix)<40 or len(self.base)<40:raise ValueError('Truncated frame')
  h=struct.unpack_from('<6I2Q',self.prefix);b=struct.unpack_from('<6I2Q',self.base)
  if h[0]!=0x3346474e or h[6]==0 or h[7]!=h[1]*280896:raise ValueError('Invalid sample envelope')
  if b[0]!=0x3346474e or b[6]==0 or b[7]!=b[1]*280896:raise ValueError('Invalid retained envelope')
  if h[1]!=b[1] or h[3:]!=b[3:]:raise ValueError('Retained tail identity mismatch')
  if self.tail_offset!=40+b[2] or sum(b[2:6])+40!=len(self.base):raise ValueError('Invalid retained sizes')
  if len(self.prefix)!=40+h[2] or len(self.base)-self.tail_offset!=sum(h[3:6]):raise ValueError('Invalid segmented sizes')
  if len(self)>64*1024*1024:raise ValueError('Unbounded frame')
 def __len__(self):return len(self.prefix)+len(self.base)-self.tail_offset
 @property
 def tail(self):return memoryview(self.base)[self.tail_offset:]
 def __bytes__(self):return self.materialize()
 def materialize(self):return b''.join((self.prefix,self.tail))
 @classmethod
 def join(cls,header,geometry,base,tail_offset):
  if type(header) is not bytes or len(header)!=40:raise ValueError('Invalid header')
  geometry=tuple(geometry)
  if len(geometry)>4094 or any(type(x) is not bytes for x in geometry):raise ValueError('Invalid geometry ownership')
  return cls(b''.join((header,*geometry)),base,tail_offset)
