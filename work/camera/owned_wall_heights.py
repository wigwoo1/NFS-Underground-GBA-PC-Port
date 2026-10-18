"""Raw wall heights, with explicit ownership required for descriptor overrides."""
import struct

def heights(wall,descriptor,camera,descriptor_offset=None):
 if len(descriptor)!=48 or len(camera)!=48:raise ValueError('Invalid height context')
 index=struct.unpack_from('<H',descriptor,10)[0]
 if index!=65535 and (descriptor_offset is None or len(descriptor_offset)!=20):raise ValueError('Missing descriptor height offset')
 base=struct.unpack_from('<i',camera,40)[0];bottom=top=base
 if index!=65535:
  bottom+=struct.unpack_from('<h',descriptor_offset,6)[0];top+=struct.unpack_from('<h',descriptor_offset,4)[0]
 result=[]
 for n in range(2):
  vertex=wall.vertices[n*68:(n+1)*68];offset=wall.offsets[n*32:(n+1)*32]
  low=bottom+struct.unpack_from('<h',vertex,56)[0];high=top+struct.unpack_from('<h',vertex,58)[0]
  if struct.unpack_from('<H',vertex,42)[0]!=65535:
   low+=struct.unpack_from('<h',offset,6)[0];high+=struct.unpack_from('<h',offset,4)[0]
  result.extend((low&0xffffffff,high&0xffffffff))
 return tuple(result)
