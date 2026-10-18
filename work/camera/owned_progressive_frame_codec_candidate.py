"""Request-scoped immutable endpoint reuse for progressive segmented frames."""
from owned_segmented_frame_candidate import SegmentedFrame
class FrameEncoder:
 def __init__(self,generation,owners=()):
  if type(owners)is not tuple or len(owners)>2 or any(type(x)is not bytes for x in owners):raise ValueError('Invalid seeded endpoints')
  self.generation=generation;self.owners=list(owners);self.raw_bytes=0;self.sent_bytes=0
 def encode(self,frame):
  if not isinstance(frame,SegmentedFrame):raise ValueError('Segmented frame required')
  self.raw_bytes+=len(frame.prefix)+len(frame.base)
  for key,owner in enumerate(self.owners):
   if owner is frame.base:base=None;break
  else:
   if len(self.owners)>=2:raise ValueError('Too many endpoint owners')
   key=len(self.owners);base=frame.base;self.owners.append(base)
  self.sent_bytes+=len(frame.prefix)+(len(base) if base is not None else 0)
  return ('segmented',self.generation,key,frame.prefix,frame.tail_offset,base)
class FrameDecoder:
 def __init__(self,generation,budget=64*1024*1024,owners=()):
  if type(owners)is not tuple or len(owners)>2 or any(type(x)is not bytes for x in owners) or sum(map(len,owners))>budget:raise ValueError('Invalid seeded endpoints')
  self.generation=generation;self.owners=list(owners);self.budget=budget;self.bytes=sum(map(len,owners))
 def decode(self,wire):
  if type(wire) is not tuple or len(wire)!=6:raise ValueError('Invalid frame wire')
  tag,generation,key,prefix,offset,base=wire
  if tag!='segmented' or generation!=self.generation or type(key) is not int or not 0<=key<2 or type(prefix) is not bytes:raise ValueError('Invalid generation or owner')
  if base is None:
   if key>=len(self.owners):raise ValueError('Unknown endpoint owner')
   owner=self.owners[key]
  else:
   if type(base) is not bytes or key!=len(self.owners) or self.bytes+len(base)>self.budget:raise ValueError('Invalid owner registration')
   owner=base
  frame=SegmentedFrame(prefix,owner,offset)
  if base is not None:self.owners.append(owner);self.bytes+=len(owner)
  return frame
 def close(self):self.owners.clear();self.bytes=0
