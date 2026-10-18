"""Derive supplemental wall invocation parents from complete owned object sources."""
import struct
from dataclasses import dataclass
from owned_scene_bundle import chunks
from owned_object_filter import select_owned,depth_distance
from owned_object_dispatch import select
@dataclass(frozen=True)
class ClosedSupplementalCall:
 association:int
 parent_descriptor:int
 object_index:int
 descriptor:int
 parent_region:tuple
 source:bytes
 snapshot:bytes

def calls(closed,supplements):
 if (closed.epoch,closed.refresh,closed.graph.refresh)!=(supplements.epoch,supplements.refresh,supplements.source_refresh):raise ValueError('Unpaired supplemental invocation')
 g=closed.graph;g.validate();objects={h[3]:(h[4],{struct.unpack_from('<I',raw,128+i*168)[0]:raw[132+i*168:296+i*168] for i in range(h[5])}) for h,raw in chunks(closed.objects,'graph_objects')};callbacks={}
 for h,raw in chunks(closed.callbacks,'callbacks'):
  if h[2]==0x03002090:callbacks.setdefault(h[7],{})[struct.unpack_from('<H',raw,32)[0]]=raw[32:196]
 available=list(chunks(supplements.geometry,'supplements'));out=[]
 for h,raw in chunks(closed.associations,'associations'):
  head,entries=objects[h[3]];completed=callbacks.get(h[7],{});parent=struct.unpack_from('<8H',raw,32)
  for index in select_owned(head,entries,g.context[256:304],completed):
   source=completed.get(index,entries[index]);dispatch=select(source,g.context[:256],depth_distance(source,g.context[256:304])[0])
   if dispatch['kind']!='supplement':continue
   region=struct.pack('<8H',dispatch['descriptor'],*parent[1:5],0,0,65535)
   matching=[i for i,(sh,sr) in enumerate(available) if sh[3]==dispatch['descriptor'] and sr[192:208]==region]
   if len(matching)!=1:raise ValueError('Unresolved owned supplemental parent')
   _,snapshot=available.pop(matching[0]);out.append(ClosedSupplementalCall(h[7],h[3],index,dispatch['descriptor'],parent,source,snapshot))
 if available:raise ValueError('Unscheduled owned supplemental snapshot')
 return tuple(out)
