"""Ordinary object draw selection from raw source and original effective depth."""
import struct
def select(source,state,depth):
 if len(source)!=164 or len(state)!=256:raise ValueError('Invalid owned dispatch source')
 flags=struct.unpack_from('<H',source,10)[0];model=struct.unpack_from('<h',source,54)[0]
 if flags&16:return dict(kind='supplement',descriptor=model&65535)
 if flags&2:depth=0
 if model>0 and depth>1024 and flags&64:depth=512
 if model==0 or depth>1024:return dict(kind='billboard',depth=depth)
 if source[136]==255:return dict(kind='hidden',depth=depth)
 index=model+(1 if depth>=512 else 0)
 return dict(kind='model',depth=depth,model=model,variant=index-model,descriptor=struct.unpack_from('<I',state,124)[0]+(index-1)*40)

