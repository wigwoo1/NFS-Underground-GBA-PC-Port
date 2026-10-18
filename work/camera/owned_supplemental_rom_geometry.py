"""Recover immutable supplemental descriptor/ring bytes from the supplied ROM."""
import struct
from dataclasses import dataclass
@dataclass(frozen=True)
class SupplementalGeometry:
 descriptor:int
 address:int
 raw_descriptor:bytes
 ring:bytes
 offset_indices:tuple
 material_indices:tuple

def recover_geometry(closed,rom):
 from owned_supplemental_dependencies import dependencies
 def read(address,size):
  offset=address-0x08000000
  if offset<0 or size<0 or offset+size>len(rom):raise ValueError('Supplemental source is not owned ROM data')
  return bytes(rom[offset:offset+size])
 vertex_base=struct.unpack_from('<I',closed.graph.context,16)[0]
 result={}
 for d in dependencies(closed):
  if d.descriptor in result:continue
  desc=read(d.descriptor_address,48)
  first,count=struct.unpack_from('<2H',desc)
  if not 0<count<=32:raise ValueError('Invalid supplemental ring count')
  ring=read(vertex_base+first*68,count*68)
  result[d.descriptor]=SupplementalGeometry(d.descriptor,d.descriptor_address,desc,ring,tuple(struct.unpack_from('<H',ring,i*68+42)[0] for i in range(count)),tuple(struct.unpack_from('<H',ring,i*68+44)[0] for i in range(count)))
 return result
