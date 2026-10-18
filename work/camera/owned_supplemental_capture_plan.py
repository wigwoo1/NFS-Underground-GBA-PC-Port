"""Build exact supplemental dynamic-state capture requirements from raw sources."""
import struct
from dataclasses import dataclass
from owned_supplemental_rom_geometry import recover_geometry
@dataclass(frozen=True)
class SourceRead:
 kind:str
 index:int
 address:int
 size:int

def capture_plan(closed,rom):
 assets=recover_geometry(closed,rom);state=closed.graph.context
 offsets={i for a in assets.values() for i in a.offset_indices if i!=65535}
 materials={i for a in assets.values() for i in a.material_indices if i!=65535}
 # Floor/ceiling materials are part of supplemental descriptor ownership too.
 materials.update(i for a in assets.values() for i in struct.unpack_from('<H',a.raw_descriptor,4)+struct.unpack_from('<H',a.raw_descriptor,8) if i!=65535)
 def records(kind,indices,slot,stride):
  base=struct.unpack_from('<I',state,slot)[0]
  for index in sorted(indices):
   address=base+index*stride
   if address+stride>0x100000000:raise ValueError('Supplemental capture address overflow')
   yield SourceRead(kind,index,address,stride)
 return tuple(records('offset',offsets,24,32))+tuple(records('material',materials,32,32))

def animation_plan(materials,animation_base):
 out={}
 for index,raw in materials.items():
  if len(raw)!=32:raise ValueError('Incomplete supplemental base material')
  animation=struct.unpack_from('<H',raw)[0];address=animation_base+animation*8
  if address+8>0x100000000:raise ValueError('Supplemental animation address overflow')
  out[animation]=SourceRead('animation',animation,address,8)
 return tuple(out[i] for i in sorted(out))
