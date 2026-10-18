"""Encode current segmented samples without materializing each retained tail."""
import struct,time
from owned_segmented_frame_candidate import SegmentedFrame
from owned_thread_cycles import read as thread_cycles

def encode_samples(samples,trace=None,borrow_tails=False):
 if borrow_tails:raise ValueError('Segmented transport requires owned immutable tail bytes')
 if not 1<=len(samples)<=8:raise ValueError('Unbounded sample count')
 tails=[];prefixes=[];encoded=[];original_bytes=0;tail_owners=[]
 for alpha,value in samples.items():
  if trace is not None:started=time.perf_counter_ns();cycles=thread_cycles()
  frame=value[0]
  if isinstance(frame,SegmentedFrame):
   prefix=frame.prefix;tail=frame.tail;end=len(prefix)
   index=next((i for i,(base,offset) in enumerate(tail_owners) if base is frame.base and offset==frame.tail_offset),None)
  elif type(frame) is bytes:
   if len(frame)<40:raise ValueError('Truncated process frame')
   end=40+struct.unpack_from('<I',frame,8)[0]
   if end>len(frame):raise ValueError('Invalid process geometry length')
   prefix=frame[:end];tail=memoryview(frame)[end:];index=None
  else:raise ValueError('Unsupported immutable process frame')
  if index is None:index=next((i for i,t in enumerate(tails) if len(t)==len(tail) and tail==t),None)
  if index is None:
   index=len(tails);tails.append(bytes(tail));tail_owners.append((frame.base,frame.tail_offset) if isinstance(frame,SegmentedFrame) else (frame,end))
  existing=next((p for p in prefixes if p==prefix),None)
  if existing is None:prefixes.append(prefix)
  else:prefix=existing
  arrays=tuple(None if x is None else bytes(x) for x in value[1:4]);original_bytes+=len(frame)+sum(len(x) for x in arrays if x is not None)
  encoded.append((alpha,(prefix,index,*arrays,value[4])))
  if trace is not None:trace.append(dict(alpha=alpha,started_ns=started,completed_ns=time.perf_counter_ns(),thread_cycles=thread_cycles()-cycles,frame_bytes=len(frame),tail_index=index))
 transferred_bytes=sum(map(len,tails))+sum(len(v[0])+sum(len(x) for x in v[2:5] if x is not None) for _,v in encoded)
 return dict(tails=tails,samples=encoded,original_bytes=original_bytes,transferred_bytes=transferred_bytes)
