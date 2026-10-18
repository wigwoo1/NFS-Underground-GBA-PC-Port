"""Owns separate geometry and immutable retained tail for synchronous GPU draws."""
import ctypes as C
from owned_segmented_frame_candidate import SegmentedFrame
from owned_source_draw_context_candidate import OwnedSourceDraw,SourceDrawContext
class SegmentedSourceContext(C.Structure):
 _fields_=[('source',SourceDrawContext),('tail',C.c_void_p),('tail_bytes',C.c_size_t)]
 @property
 def draw(self):return self.source.draw
class OwnedSegmentedSourceDraw(OwnedSourceDraw):
 def __init__(self,frame,*args):
  if not isinstance(frame,SegmentedFrame):raise ValueError('Segmented immutable owner required')
  super().__init__(frame.prefix,*args)
  self.frame=frame;tail_owner=C.c_char_p(frame.base);self.owners.append(tail_owner)
  base=C.c_void_p.from_buffer(tail_owner).value
  self.context=SegmentedSourceContext(self.context,base+frame.tail_offset,len(frame.tail))
