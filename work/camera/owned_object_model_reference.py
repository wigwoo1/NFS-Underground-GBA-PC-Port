"""Model descriptor reference selection from original owned object/state."""
import struct
def descriptors(source,state):
 if len(source)!=164 or len(state)!=256:raise ValueError('Invalid owned model reference')
 if struct.unpack_from('<H',source,10)[0]&16:return None
 flags=struct.unpack_from('<H',source,8)[0]
 if not struct.unpack_from('<H',source,72)[0] or not (flags&4 or (flags&1 and not flags&2)):return None
 identifier=struct.unpack_from('<h',source,54)[0]
 if identifier<=0:return None
 base=struct.unpack_from('<I',state,124)[0]+(identifier-1)*40
 return identifier,base,base+40
