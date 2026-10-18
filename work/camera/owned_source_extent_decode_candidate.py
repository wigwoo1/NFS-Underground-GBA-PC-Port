"""Validate topology extents without constructing per-block memoryviews."""
import struct
from owned_segmented_frame_candidate import SegmentedFrame

def extents(frame):
 if len(frame)<40:raise ValueError('Truncated owned frame')
 buffer=frame.prefix if isinstance(frame,SegmentedFrame) else frame
 magic,refresh,gn,hn,bn,tn,epoch,ticks=struct.unpack_from('<6I2Q',buffer)
 if magic!=0x3346474e or not epoch or ticks!=refresh*280896 or gn+hn+bn+tn+40!=len(frame):raise ValueError('Invalid owned frame envelope')
 offset=40;end=40+gn;counts=[]
 while offset<end:
  if end-offset<16:raise ValueError('Truncated source header')
  magic,kind,context,count=struct.unpack_from('<4I',buffer,offset);offset+=16
  if magic!=0x3147534e or kind not in (1,2,3) or count!=12:raise ValueError('Invalid source kind')
  faces=0
  for i in range(count):
   if end-offset<4:raise ValueError('Truncated source length')
   n=struct.unpack_from('<I',buffer,offset)[0];offset+=4
   if n>0x100000 or n>end-offset:raise ValueError('Invalid source block')
   if kind==3 and i==5:faces=n
   offset+=n
  counts.append(faces)
 return epoch,refresh,counts
