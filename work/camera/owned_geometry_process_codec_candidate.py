"""Isolated geometry request packing and strict seeded parent restoration."""
from owned_geometry_tail_capability_candidate import GeometryTailOwners
from owned_scene_process_transport import pack
class GeometryFrameDecoder:
 def __init__(self,generation,owners):self.capability=GeometryTailOwners(generation,owners)
 def decode(self,wire):
  if type(wire)is not tuple or len(wire)!=6:raise ValueError('Invalid geometry frame wire')
  tag,generation,key,prefix,offset,base=wire
  if tag!='segmented' or base is not None or type(offset)is not int:raise ValueError('Unseeded geometry owner reference')
  owner,header=self.capability._owner(generation,key)
  if offset!=40+header[2]:raise ValueError('Unpaired geometry owner offset')
  return self.capability.restore(generation,key,prefix)
 def close(self):self.capability.close()
def pack_geometry(frame,scene):
 packet=pack(frame,scene)
 capability=GeometryTailOwners(0,(bytes(frame),))
 try:return (capability.geometry(0,0),*packet[1:])
 finally:capability.close()
