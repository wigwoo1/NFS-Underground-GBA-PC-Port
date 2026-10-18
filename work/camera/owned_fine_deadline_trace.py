import copy,json,collections,heapq
import owned_native_transaction_interval_totals_candidate as module
Base=module.LongIntervalTotals
class DeadlineTrace(Base):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.deadline_events=[];self.deadline_total=0;self.deadline_dropped=0;self.deadline_previous=None
 def __copy__(self):
  result=super().__copy__();result.deadline_events=self.deadline_events.copy();return result
 def observe(self,row):
  super().observe(row)
  if row['native_result']!=1:return
  key=(row['epoch'],row['generation'],row['display_index']);stamp=row['commit'][6];wait=row['native_transaction']['wait'];arrival_late=max(0,wait[0]-wait[1]);gap=None
  if self.deadline_previous and key[:2]==self.deadline_previous[0][:2] and key[2]==self.deadline_previous[0][2]+1:gap=stamp-self.deadline_previous[1]
  self.deadline_previous=(key,stamp)
  if arrival_late>1000000 or (gap is not None and gap>18000000):
   event=dict(identity=key,arrival_late_ns=arrival_late,gap_ns=gap,transaction=row['native_transaction'],caller_timing=row['callback_timing'],caller_stages=row.get('caller_stages'),prepared=row.get('prepared'))
   encoded=json.dumps(event,separators=(',',':'),allow_nan=False).encode();assert len(encoded)<=16384
   self.deadline_total+=1;severity=max(arrival_late,0 if gap is None else gap-16666667)
   heapq.heappush(self.deadline_events,(severity,self.deadline_total,encoded))
   if len(self.deadline_events)>128:heapq.heappop(self.deadline_events);self.deadline_dropped+=1
 def stats(self):
  result=super().stats();result['deadline_diagnostic']=dict(total=self.deadline_total,dropped=self.deadline_dropped,capacity=128,records=[json.loads(x[2]) for x in sorted(self.deadline_events,key=lambda x:x[1])],scope='Worst128 by max(arrival lateness,gap excess16.666667ms), displayed in observation order. Dropped counts discarded low-severity records; not complete history. Arrival>1ms late or adjacent gap>18ms; diagnostic thresholds not60qualification. Native stages preserve original semantics, not scanout timestamps.');return result
module.LongIntervalTotals=DeadlineTrace

