"""Resolve original wall texture metadata from owned raw material animation."""
import struct
def resolve(base_index,animation,materials,resource_base):
 if len(animation)!=8:raise ValueError('Invalid owned animation')
 index=base_index+struct.unpack_from('<H',animation,2)[0]
 if index not in materials or len(materials[index])!=32:raise ValueError('Missing resolved material')
 source=materials[index]
 shift=struct.unpack_from('<H',source,26)[0];height=struct.unpack_from('<H',source,10)[0]
 if shift>10 or height>1024:raise ValueError('Unsupported texture dimensions')
 return dict(index=index,shift=shift,height=height,address=(resource_base+struct.unpack_from('<I',source,4)[0])&0xffffffff,bytes=(1<<shift)*height)
