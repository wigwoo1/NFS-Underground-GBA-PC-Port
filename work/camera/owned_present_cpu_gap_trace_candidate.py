"""Bounded timestamps for slow API intervals, preserving whole-run totals."""
from collections import deque
from owned_present_interval_totals_candidate import PresentationIntervalTotals as Base
class PresentationIntervalTotals(Base):
 def __init__(self):
  super().__init__();self.gaps=deque(maxlen=256);self.gaps_dropped=0
 def observe(self,row):
  previous=self.previous
  super().observe(row)
  if row['native_result']!=1 or previous is None:return
  key=(row['epoch'],row['generation'],row['display_index']);prior,start=previous
  end=row['callback_timing']['present_end_ns']
  if key[:2]!=prior[:2] or key[2]!=prior[2]+1 or end-start<=25000000:return
  if len(self.gaps)==self.gaps.maxlen:self.gaps_dropped+=1
  timing=row['callback_timing'];prepared=row.get('prepared',{})
  stages=prepared.get('consumer_stages',[])
  if len(stages)>16:raise ValueError('Unbounded slow-gap stage count')
  costs={x['stage']:x['elapsed_ns'] for x in stages}
  self.gaps.append(dict(start_ns=start,end_ns=end,display_index=key[2],epoch=key[0],generation=key[1],worker_execution=dict(prepared.get('worker_execution',{})),present_worker_execution=dict(row.get('presentation',{}).get('worker_execution',{})),native_entry_trace=list(row.get("native_entry_trace",[])),wait_trace=list(row.get("wait",[])),deadline_ns=row.get("presentation_deadline_ns"),draw_begin_ns=timing.get("draw_begin_ns"),stage_cost_ns=costs,stage_thread_cpu_ns={x["stage"]:x.get("thread_cpu_ns") for x in stages},stage_thread_cycles={x["stage"]:x.get("thread_cycles") for x in stages},stage_end_ns={x["stage"]:x.get("end_ns") for x in stages},source_prepare_ns=prepared.get('source_prepare_ns'),draw_ns=timing.get('draw_end_ns',end)-timing.get('draw_begin_ns',end),present_ns=end-timing['present_begin_ns'],prior_return_to_transaction_ns=row.get('transaction_begin_ns',start)-start,transaction_ns=row.get('transaction_end_ns',end)-row.get('transaction_begin_ns',start)))
 def __copy__(self):
  result=type(self)();result.__dict__.update(self.__dict__);result.gaps=deque(self.gaps,maxlen=256);return result
 def stats(self):
  result=super().stats();result.update(slow_gap_samples=list(self.gaps),slow_gap_dropped=self.gaps_dropped);return result
