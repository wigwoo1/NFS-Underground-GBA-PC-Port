"""Bounded scalar dequeue coverage alongside existing recent diagnostics."""
import json
from owned_serialized_recent_rows_candidate import RecentRows
class BoundaryRows(RecentRows):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.complete=[];self.complete_dropped=0
 def append(self,row):
  keys=('refresh','source_submitted_ns','notification_wait_begin_ns','loop_started_ns','input_ready_ns','previous_frame_free_ns','previous_frame_free_execution','held_frame_free','dequeued_ns','popped_ns','snapshot_ready_ns','copied_ns','matched_ns','frame_bytes','try_pop_attempts','try_pop_status')
  compact={k:row[k] for k in keys}; encoded=json.dumps(compact,separators=(',',':'),allow_nan=False)
  assert len(encoded.encode())<=2048
  super().append(row)
  if len(self.complete)<4096:self.complete.append(encoded)
  else:self.complete_dropped+=1
 def stats(self):
  out=super().stats();out['complete_dequeues']=dict(total=self.total_records,dropped=self.complete_dropped,capacity=4096,max_record_bytes=2048,records=[json.loads(x) for x in self.complete],scope='Every scalar dequeue only when dropped==0; no frame ownership or scheduling change.')
  return out
