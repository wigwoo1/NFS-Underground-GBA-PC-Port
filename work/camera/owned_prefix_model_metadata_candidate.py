"""Experimental exact immutable prefix reuse; no default renderer selection."""
import threading,time
from owned_sample_model_metadata_candidate import decode
from owned_segmented_frame_candidate import SegmentedFrame
local=threading.local();stats=dict(hits=0,misses=0,bypasses=0);MAX_BYTES=64*1024*1024
def clear():local.entries=[]
def records(frame,trace=None):
 start=time.perf_counter_ns() if trace is not None else 0
 if type(frame) is SegmentedFrame:
  # Check every envelope/tail even when geometry's exact immutable owner repeats.
  frame.__post_init__();owner=frame.prefix
 elif type(frame) is bytes and len(frame)<=MAX_BYTES:owner=frame
 else:owner=None;stats['bypasses']+=1
 entries=getattr(local,'entries',[]) if owner is not None else []
 for old,result in entries:
  if old is owner:stats['hits']+=1;break
 else:
  result=decode(frame);stats['misses']+=1
  if owner is not None:
   retained=[*entries,(owner,result)][-2:]
   while retained and sum(len(x[0]) for x in retained)>MAX_BYTES:retained.pop(0)
   local.entries=retained
 if trace is not None:
  end=time.perf_counter_ns();trace.append(dict(name='exact_prefix_model_metadata',started_ns=start,completed_ns=end,wall_ns=end-start))
 return dict(refresh=result['refresh'],epoch=result['epoch'],ticks=result['ticks'],records=[dict(kind=r['kind'],context=r['context'],key=r['key'],blocks=list(r['blocks'])) for r in result['records']])
