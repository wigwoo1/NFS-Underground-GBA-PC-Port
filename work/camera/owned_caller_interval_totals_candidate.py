"""Bounded immutable long-interval evidence; caller timing unchanged."""
import copy,json
from collections import deque
from owned_present_interval_totals_candidate import PresentationIntervalTotals
class LongIntervalTotals(PresentationIntervalTotals):
 def __init__(self,capacity=512):
  super().__init__();self.capacity=capacity;self.long_events=deque();self.long_total=0;self.long_dropped=0
 def __copy__(self):
  new=type(self).__new__(type(self));new.__dict__=self.__dict__.copy();new.long_events=self.long_events.copy();return new
 def observe(self,row):
  previous=self.previous;count=self.count;super().observe(row)
  if self.count==count or previous is None:return
  begin=previous[1];end=self.previous[1]
  if (end-begin)*3<=100000000:return
  prepared=row.get('prepared') or {};timing=row['callback_timing']
  event=dict(epoch=row['epoch'],generation=row['generation'],display_index=row['display_index'],begin_ns=begin,end_ns=end,interval_ns=end-begin,draw_begin_ns=timing['draw_begin_ns'],draw_end_ns=timing['draw_end_ns'],present_begin_ns=timing['present_begin_ns'],present_end_ns=timing['present_end_ns'],source_prepare_ns=prepared.get('source_prepare_ns'),hud_lease_stages=prepared.get('hud_lease_stages'),hud_build_split=prepared.get('hud_build_split'),renderer_dispatch=prepared.get('renderer_dispatch'),consumer_stages=prepared.get('consumer_stages'),caller_stages=row.get('caller_stages'),transaction_begin_ns=row.get('transaction_begin_ns'),transaction_end_ns=row.get('transaction_end_ns'))
  encoded=json.dumps(event,separators=(',',':'),allow_nan=False).encode();assert len(encoded)<=16384
  self.long_events.append(encoded);self.long_total+=1
  if len(self.long_events)>self.capacity:self.long_events.popleft();self.long_dropped+=1
 def stats(self):
  out=super().stats();out['long_intervals']=dict(total=self.long_total,dropped=self.long_dropped,capacity=self.capacity,records=[json.loads(x) for x in self.long_events],scope='Intervals>33.333ms excludingpause/generationdiscontinuities; APIreturntimes, notpixel/scanout proof. Bounded512records16KiB each.')
  return out
