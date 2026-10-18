"""Isolated bounded immutable endpoint validation summary reuse."""
import threading
from owned_motion_pairs import _decode_records
from owned_closed_graph import ClosedGraph
local=threading.local();MAX_BYTES=64*1024*1024;MAX_ENTRIES=2
stats=dict(hits=0,misses=0,bypasses=0)
original=ClosedGraph.match_frame
def summary(frame):
 cacheable=type(frame) is bytes and len(frame)<=MAX_BYTES
 entries=getattr(local,'entries',[])
 if cacheable:
  for i,(owner,value) in enumerate(entries):
   if owner is frame:
    stats['hits']+=1;entries.append(entries.pop(i));return value
  stats['misses']+=1
 else:stats['bypasses']+=1
 scene=_decode_records(frame,source_keys=False)
 cameras=tuple(bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in scene['records'] if r['kind'] in (1,2))
 value=(scene['epoch'],scene['refresh'],cameras)
 if cacheable:
  entries.append((frame,value))
  while len(entries)>MAX_ENTRIES or sum(len(x[0]) for x in entries)>MAX_BYTES:entries.pop(0)
  local.entries=entries
 return value
def match_frame(self,frame):
 epoch,refresh,cameras=summary(frame)
 if epoch!=self.epoch or refresh!=self.refresh:raise ValueError('Closed graph/frame identity mismatch')
 if not cameras or any(c!=self.graph.context[256:304] for c in cameras):raise ValueError('Closed graph/frame camera mismatch')
def clear():local.entries=[]
def install():ClosedGraph.match_frame=match_frame
def uninstall():ClosedGraph.match_frame=original
