"""Bounded observational collection ledger; GC policy unchanged."""
import gc,time,threading
class CollectionTrace:
 def __init__(self,limit=5000):self.limit=limit;self.rows=[];self.pending=None;self.dropped=0;self.callback=self.observe;gc.callbacks.append(self.callback)
 def observe(self,phase,info):
  if phase=='start':self.pending=(time.perf_counter_ns(),threading.get_ident(),info['generation'],time.thread_time_ns())
  elif phase=='stop' and self.pending is not None:
   begin,owner,generation,cpu_begin=self.pending;self.pending=None
   if len(self.rows)<self.limit:self.rows.append(dict(start_ns=begin,end_ns=time.perf_counter_ns(),thread_id=owner,generation=generation,thread_cpu_ns=time.thread_time_ns()-cpu_begin,collected=info['collected'],uncollectable=info['uncollectable']))
   else:self.dropped+=1
 def close(self):
  if self.callback in gc.callbacks:gc.callbacks.remove(self.callback)
