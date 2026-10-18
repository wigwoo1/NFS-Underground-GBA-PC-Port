"""Full validated row decode; source hashes only for model consumers."""
import time,threading
from owned_thread_cycles import read as thread_cycles
from owned_motion_pairs import _decode_records
from owned_segmented_frame_candidate import SegmentedFrame
_model_record_cache=threading.local()
def records(frame,trace=None):
 def mark(name,**details):
  nonlocal started,cycles
  now=time.perf_counter_ns();current=thread_cycles()
  trace.append(dict(name=name,started_ns=started,completed_ns=now,wall_ns=now-started,thread_cycles=current-cycles,**details));started=now;cycles=current
 if trace is not None:started=time.perf_counter_ns();cycles=thread_cycles()
 if type(frame) is not bytes and not isinstance(frame,SegmentedFrame):
  decode_trace=[] if trace is not None else None
  result=_decode_records(frame,source_keys="models",decode_trace=decode_trace)
  if trace is not None:mark('mutable_decode',records=len(result['records']),frame_bytes=len(frame))
  return result
 entries=getattr(_model_record_cache,'entries',[])
 for owner,header,rows in entries:
  if owner is frame:break
 else:
  if trace is not None:mark('cache_lookup',hit=False,entries=len(entries))
  decode_trace=[] if trace is not None else None
  result=_decode_records(frame,source_keys="models",decode_trace=decode_trace)
  if trace is not None:mark('uncached_decode',records=len(result['records']),frame_bytes=len(frame),refresh=result['refresh'],decode_rows=decode_trace)
  header=(result['refresh'],result['epoch'],result['ticks'])
  rows=tuple((r['kind'],r['context'],tuple(r['blocks']),r['key']) for r in result['records'])
  if trace is not None:mark('cache_metadata_pack')
  entries.append((frame,header,rows));_model_record_cache.entries=entries[-4:]
  # Release previous cache-list ownership within the measured stage.
  del entries
  if trace is not None:mark('cache_replace')
  result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])
  if trace is not None:mark('caller_containers')
  return result
 if trace is not None:mark('cache_lookup',hit=True,entries=len(entries))
 result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])
 if trace is not None:mark('caller_containers')
 return result
