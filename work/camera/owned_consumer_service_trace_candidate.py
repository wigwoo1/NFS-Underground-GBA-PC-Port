"""Bounded actual admission setup timing, including fully retired pairs."""
import time,json,threading
from collections import deque
from pathlib import Path
rows=deque(maxlen=8192);total=0;dropped=0
local=threading.local()
identity_lock=threading.Lock();identity_serial=0
def future_identity(future):
 global identity_serial
 with identity_lock:
  value=getattr(future,'_consumer_trace_identity',None)
  if value is None:
   identity_serial+=1;value=identity_serial;future._consumer_trace_identity=value
  return value
publication_rows=deque(maxlen=8192);publication_total=0;publication_dropped=0
from owned_progressive_pair_candidate import ProgressivePair
original_publish=ProgressivePair.publish
def traced_publish(self,packet):
 global publication_total,publication_dropped
 first=self.first;first_pending=not first.done();begin=time.perf_counter_ns()
 result=original_publish(self,packet)
 if first_pending:
  publication_total+=1
  if len(publication_rows)==publication_rows.maxlen:publication_dropped+=1
  publication_rows.append(dict(future_identity=future_identity(first),begin_ns=begin,end_ns=time.perf_counter_ns()))
 return result
ProgressivePair.publish=traced_publish
upstream_rows=deque(maxlen=8192);upstream_total=0;upstream_dropped=0
from owned_progressive_parent_service_candidate import ProgressiveService
original_start=ProgressiveService.start;original_service_take=ProgressiveService.take
upstream_local=threading.local()
def traced_start(self,older,newer,alphas):
 begin=time.perf_counter_ns();result=original_start(self,older,newer,alphas)
 upstream_local.request=dict(older=older[1].identity[1],newer=newer[1].identity[1],generation=self.generation,start_begin_ns=begin,start_end_ns=time.perf_counter_ns())
 return result
def traced_service_take(self,timeout=20):
 global upstream_total,upstream_dropped
 result=original_service_take(self,timeout)
 if self.count==1:
  row=dict(upstream_local.request,**{k:self.last_sample_timing[k] for k in ('receive_begin_ns','received_ns','decoded_ns')})
  upstream_total+=1
  if len(upstream_rows)==upstream_rows.maxlen:upstream_dropped+=1
  upstream_rows.append(row)
 return result
ProgressiveService.start=traced_start;ProgressiveService.take=traced_service_take
terminal_rows=deque(maxlen=8192);terminal_total=0;terminal_dropped=0
original_terminal=ProgressiveService._terminal
def traced_terminal(self,message):
 global terminal_total,terminal_dropped
 result=original_terminal(self,message)
 detail=message[5];samples=detail.get('sample_transfer_rows',[])
 fine_stages=[]
 for group in ('construct_stages','source_setup_stages'):
  for stage in detail.get(group,[]):
   if isinstance(stage,dict):
    fine_stages.append({k:stage[k] for k in ('name','wall_ns','started_ns','completed_ns') if k in stage})
    for sub in stage.get('asset_stages',[]):
     fine_stages.append(dict(name=stage['name']+'/'+sub['name'],wall_ns=sub['wall_ns']))
 row=dict(upstream_local.request,fine_stages=fine_stages,status=message[2],sample_count=message[3],child_started_ns=detail['child_started_ns'],decoded_ns=detail['decoded_ns'],initialized_ns=detail['initialized_ns'],constructed_ns=detail['constructed_ns'],first_sample=None if not samples else {k:samples[0][k] for k in ('ready_ns','encode_ns','send_ns','ack_wait_ns')})
 terminal_total+=1
 if len(terminal_rows)==terminal_rows.maxlen:terminal_dropped+=1
 terminal_rows.append(row)
 return result
ProgressiveService._terminal=traced_terminal

from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter
original_take=ProgressivePreparationAdapter.take
class FutureTimingProxy:
 def __init__(self,future):object.__setattr__(self,'future',future);object.__setattr__(self,'result_return_ns',None)
 def __getattr__(self,name):return getattr(self.future,name)
 def __setattr__(self,name,value):setattr(self.future,name,value)
 def result(self,timeout):
  value=self.future.result(timeout);object.__setattr__(self,'result_return_ns',time.perf_counter_ns());return value
def traced_take(self,future,timeout=30):
 begin=time.perf_counter_ns();local.future_identity=future_identity(future);proxy=FutureTimingProxy(future)
 try:return original_take(self,proxy,timeout)
 finally:local.take=(begin,proxy.result_return_ns,time.perf_counter_ns())
ProgressivePreparationAdapter.take=traced_take
def admission_started(started,older,newer,epoch,generation,take_begin,take_end):
 global total,dropped
 result_return=None
 if hasattr(local,"take"):
  take_begin,result_return,take_end=local.take;del local.take
 total+=1
 if len(rows)==rows.maxlen:dropped+=1
 rows.append(dict(started_ns=started,admission_started_ns=time.perf_counter_ns(),older=older,newer=newer,epoch=epoch,generation=generation,take_begin_ns=take_begin,take_end_ns=take_end,result_return_ns=result_return,future_identity=getattr(local,"future_identity",None)))
def save():
 path=Path('work/camera/prototype-runs')/('consumer-service-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(total=total,dropped=dropped,records=list(rows),terminal_total=terminal_total,terminal_dropped=terminal_dropped,terminal_records=list(terminal_rows),upstream_total=upstream_total,upstream_dropped=upstream_dropped,upstream_records=list(upstream_rows),publication_total=publication_total,publication_dropped=publication_dropped,publications=list(publication_rows),scope='Actual pair_begin through admission boundary inclusive wall time, including preparation waits; no complete consumer service or exclusive CPU/cadence claim.'),indent=2));print('CONSUMER_SERVICE',path,total,dropped,flush=True)
