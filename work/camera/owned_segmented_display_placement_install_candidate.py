from owned_native_source_segmented_session_candidate import NativeSourceSession as Base
from owned_uncovered_window_candidate import OwnedD3DConsumer,placements
from owned_dxgi_linked_span_totals_candidate import DisplayProgressTotals
import owned_native_source_segmented_session_candidate as session_module
import owned_native_source_segmented_release_worker_candidate as worker_module
from collections import deque
from owned_window_overlap_candidate import inspect
coverage_rows=deque(maxlen=16)
progress=DisplayProgressTotals()
raw_rows=deque(maxlen=120);status_counts={};raw_total=0
class DisplaySession(Base):
 def present(self,epoch,generation,index):
  global raw_total
  result=super().present(epoch,generation,index)
  raw_total+=1;key=str(result["status"]);status_counts[key]=status_counts.get(key,0)+1
  if raw_total%120==1:coverage_rows.append(dict(index=index,**inspect(result["window"][6])))
  raw_rows.append(dict(epoch=epoch,generation=generation,index=index,**result))
  progress.observe((epoch,generation),result['dxgi_display_stats'],dict(epoch=epoch,generation=generation,display_index=index))
  return result
session_module.OwnedD3DConsumer=OwnedD3DConsumer
worker_module.NativeSourceSession=DisplaySession

def diagnostic_stats():return dict(progress=progress.stats(),raw_recent=list(raw_rows),raw_total=raw_total,present_status_counts=status_counts.copy(),window_overlap_recent=list(coverage_rows),window_placement=placements)



