"""Opt-in per-thread two-entry immutable graph/frame validation cache, bounded32MiB."""
import threading
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
local=threading.local();stats=dict(checks=0,hits=0,validated=0,uncached=0)
original=ClosedGraph.match_frame
BUDGET=32*1024*1024
def match_frame(self,frame):
 stats['checks']+=1
 immutable=type(self)is ClosedGraph and type(self.graph)is GraphPacket and type(frame)is bytes
 if immutable:
  for owner in getattr(local,'entries',()):
   if owner[0] is self and owner[1] is frame:
    stats['hits']+=1;return
 original(self,frame);stats['validated']+=1
 if immutable:
  g=self.graph
  size=len(frame)+sum(len(x) for x in (g.context,g.geometry,g.offsets,g.materials,g.faces,self.objects,self.callbacks,self.associations))
  if size<=BUDGET:
   entries=list(getattr(local,'entries',()))
   while entries and (len(entries)>=2 or sum(x[2] for x in entries)+size>BUDGET):entries.pop(0)
   entries.append((self,frame,size));local.entries=entries;return
 stats['uncached']+=1;local.entries=[]
ClosedGraph.match_frame=match_frame
