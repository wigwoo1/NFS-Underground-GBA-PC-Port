"""Diagnostic per-model source-mask cost; same classifier decisions."""
import types
import owned_fixed_types_process_service_candidate as fixed
from owned_bounded_fixed_types_service_candidate import BoundedProcessService as Base
def request_child(connection,rom,shared_output,request_name):
 import time,json,os
 from pathlib import Path
 from collections import deque
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants as Original
 rows=deque();total=0;dropped=0
 class Profiled(Original):
  def __init__(self,older,newer,*args):
   self.profile_key=older['key'];super().__init__(older,newer,*args)
  def combined_decisions(self,m,alpha,rect):
   nonlocal total,dropped
   start=time.perf_counter_ns();cpu=time.thread_time_ns()
   result=super().combined_decisions(m,alpha,rect)
   end=time.perf_counter_ns();elapsed=end-start
   if elapsed>2000000:
    total+=1;rows.append(dict(key=self.profile_key,alpha=alpha,start_ns=start,end_ns=end,wall_ns=elapsed,cpu_ns=time.thread_time_ns()-cpu,vertices=len(self.vertices),faces=len(self.faces),single_endpoint=self.single_endpoint,endpoint_valid=self.endpoint_valid,visible=sum(result[0]),rectangle_rejected=sum(v==4 for v in result[1])))
    if len(rows)>512:rows.popleft();dropped+=1
   return result
 batch.SourceFaceDeterminants=Profiled
 try:fixed.request_child(connection,rom,shared_output,request_name)
 finally:
  Path('work/camera/prototype-runs/mask-model-profile-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),total=total,dropped=dropped,rows=list(rows),scope='Diagnostic wall/threadCPU by actual classifier; no decision changes, no cadence qualification.'),indent=2))
class ProcessPreparationService(Base):pass
original=fixed.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
