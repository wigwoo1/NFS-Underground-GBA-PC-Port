"""Complete envelope/block validation with camera-only payload views."""
import struct
from owned_closed_graph import ClosedGraph as Original
from owned_segmented_frame_candidate import SegmentedFrame
class ClosedGraph(Original):
 def match_frame(self,frame):
  if len(frame)<40:raise ValueError('Truncated owned frame')
  buffer=frame.prefix if isinstance(frame,SegmentedFrame) else frame
  magic,refresh,gn,hn,bn,tn,epoch,ticks=struct.unpack_from('<6I2Q',buffer)
  if magic!=0x3346474e or not epoch or ticks!=refresh*280896 or gn+hn+bn+tn+40!=len(frame):raise ValueError('Invalid owned frame envelope')
  g=memoryview(buffer)[40:40+gn];offset=0;cameras=0;mismatch=False;camera=self.graph.context[256:304]
  while offset<len(g):
   if len(g)-offset<16:raise ValueError('Truncated source header')
   magic,kind,context,count=struct.unpack_from('<4I',g,offset);offset+=16
   if magic!=0x3147534e or kind not in (1,2,3) or count!=12:raise ValueError('Invalid source kind')
   for i in range(count):
    if len(g)-offset<4:raise ValueError('Truncated source length')
    n=struct.unpack_from('<I',g,offset)[0];offset+=4
    if n>0x100000 or n>len(g)-offset:raise ValueError('Invalid source block')
    if kind in (1,2) and i==(4 if kind==1 else 3):
     cameras+=1;mismatch=mismatch or g[offset:offset+n]!=camera
    offset+=n
  if epoch!=self.epoch or refresh!=self.refresh:raise ValueError('Closed graph/frame identity mismatch')
  if not cameras or mismatch:raise ValueError('Closed graph/frame camera mismatch')
