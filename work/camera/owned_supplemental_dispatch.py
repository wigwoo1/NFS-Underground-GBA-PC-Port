"""Supplemental region invocations derived from owned callback-complete objects."""
import struct
from dataclasses import dataclass
from owned_scene_dispatch import draws
from owned_scene_bundle import chunks

@dataclass(frozen=True)
class SupplementalCall:
 region_ordinal:int
 object_index:int
 descriptor:int
 region:bytes
 snapshot:bytes

def calls(bundle):
 bundle.validate();associations={h[7]:raw[32:48] for h,raw in chunks(bundle.associations,'associations')};available=list(chunks(bundle.supplements,'supplements'));result=[]
 for draw in draws(bundle):
  dispatch=draw['dispatch']
  if dispatch['kind']!='supplement':continue
  parent=struct.unpack('<8H',associations[draw['region']]);region=struct.pack('<8H',dispatch['descriptor'],*parent[1:5],0,0,65535)
  matches=[(i,h,raw) for i,(h,raw) in enumerate(available) if h[3]==dispatch['descriptor'] and raw[192:208]==region]
  if len(matches)!=1:raise ValueError('Missing or ambiguous owned supplemental call asset')
  i,h,raw=matches[0];available.pop(i)
  result.append(SupplementalCall(draw['region'],draw['index'],dispatch['descriptor'],region,raw))
 if available:raise ValueError('Unscheduled supplemental asset')
 return tuple(result)
