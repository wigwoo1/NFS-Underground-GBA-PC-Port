"""Track actual commit completion independently from delayed Python return."""
import copy,json
from collections import deque
from owned_d3d_wait_25ms_interval_totals_candidate import LongIntervalTotals as Base
class LongIntervalTotals(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.native_events=deque();self.native_dropped=0;self.native_long_total=0;self.native_previous=None;self.native_count=0;self.native_excluded=0;self.native_total=0;self.native_max=0;self.native_over25=0;self.native_over33=0;self.native_over50=0;self.native_under8=0;self.native_min=None;self.native_late_count=0;self.native_late_total=0;self.native_late_max=0
  self.all_native_events=deque();self.all_native_samples=0;self.all_native_count=0;self.all_native_excluded=0;self.all_native_total=0;self.all_native_max=0;self.all_native_over25=0;self.all_native_over33=0;self.all_native_over50=0;self.all_native_skipped=0;self.all_native_long_total=0;self.all_native_dropped=0
  self.first_success_ns=None;self.first_success_deadline_ns=None;self.last_success_ns=None
  self.native_segments=deque();self.native_segments_total=0;self.native_segments_dropped=0;self.native_first_events=deque();self.native_first_dropped=0
 def __copy__(self):
  new=super().__copy__();new.native_first_events=self.native_first_events.copy();new.native_events=self.native_events.copy();new.all_native_events=self.all_native_events.copy();new.native_segments=deque(dict(x) for x in self.native_segments);return new
 def observe(self,row):
  super().observe(row)
  if row['native_result']!=1:return
  wait=row['native_transaction']['wait'];assert len(wait)==4 and wait[2]>=wait[0]
  late=max(0,wait[0]-wait[1]);self.native_late_count+=late>0;self.native_late_total+=late;self.native_late_max=max(self.native_late_max,late)
  stamp=row['commit'][6];key=(row['epoch'],row['generation'],row['display_index'])
  if self.first_success_ns is None:self.first_success_ns=stamp;self.first_success_deadline_ns=wait[1]
  self.last_success_ns=stamp
  if not self.native_segments or (self.native_segments[-1]['epoch'],self.native_segments[-1]['generation'])!=key[:2]:
   event=dict(epoch=key[0],generation=key[1],display_index=key[2],end_ns=stamp,transaction=row['native_transaction'],caller_timing=row['callback_timing'],prepared=row.get('prepared'),caller_stages=row.get('caller_stages'))
   encoded=json.dumps(event,separators=(',',':'),allow_nan=False).encode()
   if len(encoded)>16384:raise ValueError('Native first-success record exceeds bound')
   self.native_first_events.append(encoded)
   if len(self.native_first_events)>self.capacity:self.native_first_events.popleft();self.native_first_dropped+=1
   self.native_segments.append(dict(epoch=key[0],generation=key[1],first_success_ns=stamp,first_success_deadline_ns=wait[1],last_success_ns=stamp,first_index=key[2],last_index=key[2],successful_samples=1));self.native_segments_total+=1
   if len(self.native_segments)>self.capacity:self.native_segments.popleft();self.native_segments_dropped+=1
  else:
   segment=self.native_segments[-1]
   if stamp<segment['last_success_ns'] or key[2]<=segment['last_index']:raise ValueError('Native segment regressed')
   segment['last_success_ns']=stamp;segment['last_index']=key[2];segment['successful_samples']+=1
  self.all_native_samples+=1
  if self.native_previous:
   prior,at=self.native_previous
   if key[:2]==prior[:2]:
    delta=stamp-at;index_delta=key[2]-prior[2]
    if delta<0 or index_delta<=0:raise ValueError('Successful native identity/timestamp regressed')
    self.all_native_count+=1;self.all_native_total+=delta;self.all_native_max=max(self.all_native_max,delta);self.all_native_over25+=delta>25000000;self.all_native_over33+=delta*3>100000000;self.all_native_over50+=delta>50000000;self.all_native_skipped+=index_delta-1
    if delta>25000000:
     event=dict(epoch=key[0],generation=key[1],previous_index=prior[2],display_index=key[2],index_delta=index_delta,begin_ns=at,end_ns=stamp,interval_ns=delta)
     encoded=json.dumps(event,separators=(',',':')).encode();assert len(encoded)<=512
     self.all_native_events.append(encoded);self.all_native_long_total+=1
     if len(self.all_native_events)>self.capacity:self.all_native_events.popleft();self.all_native_dropped+=1
   else:self.all_native_excluded+=1
   if key[:2]==prior[:2] and key[2]==prior[2]+1:
    delta=stamp-at
    if delta<0:raise ValueError('Native commit timestamp regressed')
    if delta>25000000:
     event=dict(begin_ns=at,end_ns=stamp,interval_ns=delta,epoch=key[0],generation=key[1],display_index=key[2],transaction=row['native_transaction'],caller_timing=row['callback_timing'],prepared=row.get('prepared'),caller_stages=row.get('caller_stages'))
     encoded=json.dumps(event,separators=(',',':'),allow_nan=False).encode()
     if len(encoded)>16384:raise ValueError('Native interval record exceeds bound')
     self.native_events.append(encoded);self.native_long_total+=1
     if len(self.native_events)>self.capacity:self.native_events.popleft();self.native_dropped+=1
    self.native_under8+=delta<8000000;self.native_min=delta if self.native_min is None else min(self.native_min,delta);self.native_count+=1;self.native_total+=delta;self.native_max=max(self.native_max,delta);self.native_over25+=delta>25000000;self.native_over33+=delta*3>100000000;self.native_over50+=delta>50000000
   else:self.native_excluded+=1
  self.native_previous=(key,stamp)
 def coverage(self,begin_ns,end_ns):
  if type(begin_ns) is not int or type(end_ns) is not int or begin_ns<0 or end_ns<begin_ns:raise ValueError('Invalid observation interval')
  if self.first_success_ns is None:return dict(successful_samples=0,initial_hold_ns=end_ns-begin_ns,trailing_hold_ns=end_ns-begin_ns,qualified=False)
  if begin_ns>self.first_success_ns or end_ns<self.last_success_ns:raise ValueError('Observation excludes successful frames')
  return dict(successful_samples=self.all_native_samples,initial_hold_ns=self.first_success_ns-begin_ns,trailing_hold_ns=end_ns-self.last_success_ns,qualified=False,scope='Explicit external observation boundaries; holds include pause if present. No automatic cadence qualification.')
 def stats(self):
  out=super().stats();out['native_commit_intervals']=dict(count=self.native_count,excluded=self.native_excluded,mean_ms=self.native_total/self.native_count/1e6 if self.native_count else None,max_ms=self.native_max/1e6,over25=self.native_over25,over33=self.native_over33,over50=self.native_over50,under8=self.native_under8,min_ms=None if self.native_min is None else self.native_min/1e6,deadline_late_count=self.native_late_count,deadline_late_total_ms=self.native_late_total/1e6,deadline_late_max_ms=self.native_late_max/1e6,scope='Actual successful native commit completion timestamps, adjacent index within same epoch/generation only; no pixel/scanout proof.')
  out['native_commit_long_intervals']=dict(total=self.native_long_total,dropped=self.native_dropped,capacity=self.capacity,record_byte_limit=16384,records=[json.loads(x) for x in self.native_events])
  out['all_successful_native_intervals']=dict(successful_samples=self.all_native_samples,count=self.all_native_count,excluded_generation_discontinuities=self.all_native_excluded,mean_ms=self.all_native_total/self.all_native_count/1e6 if self.all_native_count else None,max_ms=self.all_native_max/1e6,over25=self.all_native_over25,over33=self.all_native_over33,over50=self.all_native_over50,skipped_indices_between_successes=self.all_native_skipped,scope='Every successful completion interval within same epoch/generation, including skipped display indices. Pause/reset transitions excluded explicitly; no scanout qualification.')
  out['native_success_segments']=dict(total=self.native_segments_total,dropped=self.native_segments_dropped,capacity=self.capacity,records=[dict(x) for x in self.native_segments],scope='Bounded per epoch/generation success boundaries; external pause/reset/observation bounds and zero-success segments required for coverage. No automatic qualification.')
  out['native_first_success_records']=dict(total=self.native_segments_total,dropped=self.native_first_dropped,capacity=self.capacity,record_byte_limit=16384,records=[json.loads(x) for x in self.native_first_events])
  out['native_success_boundaries']=dict(first_success_ns=self.first_success_ns,first_success_deadline_ns=self.first_success_deadline_ns,last_success_ns=self.last_success_ns,successful_samples=self.all_native_samples,scope='Whole observed success stream; external active observation bounds still required to measure initial/trailing holds.')
  out['all_successful_native_long_intervals']=dict(total=self.all_native_long_total,dropped=self.all_native_dropped,capacity=self.capacity,record_byte_limit=512,records=[json.loads(x) for x in self.all_native_events])
  return out


