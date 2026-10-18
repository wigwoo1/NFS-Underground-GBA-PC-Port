"""Original ordinary object sprite/material selection from raw owned sources."""
import struct
def reference(source,state,depth,read):
 if len(source)!=164 or len(state)!=256:raise ValueError('Invalid owned object texture source')
 u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
 u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
 flags=u16(source,10);model=struct.unpack_from('<h',source,54)[0]
 if flags&2:depth=0
 lod=1 if model>0 and depth>1024 and not flags&64 else 0
 index=u16(source,72)+lod+u16(source,70)+(u16(source,68)>>8)
 sprite=u32(state,36)+index*32;material=bytes(read(sprite,32))
 if len(material)!=32:raise ValueError('Missing owned sprite material')
 if flags&8:
  address=u32(source,132)
  if depth>1024:
   previous=read(sprite-32,32);address+=u16(previous,8)*u16(previous,10)
 else:address=u32(state,4)+u32(material,4)
 return sprite,address&0xffffffff,u16(material,26),u16(material,10)
