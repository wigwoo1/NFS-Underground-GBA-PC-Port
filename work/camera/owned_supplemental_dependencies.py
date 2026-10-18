"""Enumerate supplemental asset dependencies without requiring a visible invocation."""
import struct
from dataclasses import dataclass
from owned_scene_bundle import chunks

@dataclass(frozen=True)
class SupplementalDependency:
 parent_descriptor:int
 object_index:int
 descriptor:int
 descriptor_address:int
 source:bytes

def dependencies(closed):
 # Enumerate complete chains, including objects culled at both motion endpoints.
 # Eligibility and callback state must be resolved separately during dispatch.
 state=closed.graph.context[:256]
 base=struct.unpack_from('<I',state,20)[0]
 out=[]
 for h,raw in chunks(closed.objects,'graph_objects'):
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0]
   source=bytes(raw[132+i*168:296+i*168])
   if len(source)!=164:raise ValueError('Truncated supplemental object')
   if not struct.unpack_from('<H',source,10)[0]&16:continue
   descriptor=struct.unpack_from('<H',source,54)[0]
   address=base+descriptor*48
   if address>0xffffffff:raise ValueError('Supplemental descriptor address overflow')
   out.append(SupplementalDependency(h[3],index,descriptor,address,source))
 return tuple(out)
