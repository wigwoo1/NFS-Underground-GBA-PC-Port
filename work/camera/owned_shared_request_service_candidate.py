"""Isolated bounded copied requests with explicit read acknowledgement."""
import inspect,textwrap,time
from multiprocessing.shared_memory import SharedMemory
from owned_shared_blob import SharedBlobOwner
from owned_shared_payload import write_payload,read_payload
import owned_segmented_shared_process_service_candidate as output
import owned_source_process_service_candidate as base
class ParentConnection:
 def __init__(self,connection,owner):self.connection=connection;self.owner=owner;self.serial=0;self.failed=False;self.acknowledged=0;self.stage_totals={name:dict(count=0,total_ns=0,max_ns=0) for name in ("mapping_write","descriptor_send","ack_wait")}
 def send(self,value):
  if isinstance(value,tuple) and len(value)==5:
   if self.failed:raise RuntimeError('Shared request channel failed')
   began=time.perf_counter_ns()
   self.serial+=1;descriptor=write_payload(self.owner.memory,value,value[0],self.serial)
   written=time.perf_counter_ns()
   self.connection.send(('request_shared',descriptor))
   sent=time.perf_counter_ns()
   if not self.connection.poll(30):self.failed=True;raise RuntimeError('Shared request acknowledgement stalled')
   if self.connection.recv()!=('request_ack',descriptor):self.failed=True;raise RuntimeError('Shared request acknowledgement mismatch')
   acknowledged=time.perf_counter_ns()
   self.acknowledged+=1
   for name,duration in (("mapping_write",written-began),("descriptor_send",sent-written),("ack_wait",acknowledged-sent)):
    row=self.stage_totals[name];row["count"]+=1;row["total_ns"]+=duration;row["max_ns"]=max(row["max_ns"],duration)
  else:self.connection.send(value)
 def recv(self):return self.connection.recv()
 def poll(self,*args):return self.connection.poll(*args)
 def close(self):self.connection.close()
 @property
 def closed(self):return self.connection.closed
class ChildConnection:
 def __init__(self,connection,name):self.connection=connection;self.memory=SharedMemory(name=name);self.serial=0
 def recv(self):
  value=self.connection.recv()
  if isinstance(value,tuple) and len(value)==2 and value[0]=='request_shared':
   descriptor=value[1]
   try:
    if not isinstance(descriptor,tuple) or len(descriptor)!=4 or descriptor[0]!=self.memory.name or descriptor[2]!=self.serial+1:raise ValueError('Invalid shared request owner or serial')
    request=read_payload(descriptor,descriptor[1],self.memory)
    if not isinstance(request,tuple) or len(request)!=5 or request[0]!=descriptor[1]:raise ValueError('Invalid shared request envelope')
   except BaseException:
    self.connection.send(('request_error',descriptor));raise
   self.serial=descriptor[2];self.connection.send(('request_ack',descriptor));return request
  return value
 def send(self,value):self.connection.send(value)
 def poll(self,*args):return self.connection.poll(*args)
 def close(self):
  try:self.connection.close()
  finally:self.memory.close()
def request_child(connection,rom,shared_output,request_name):
 wrapped=ChildConnection(connection,request_name)
 try:output.shared_segmented_child(wrapped,rom,shared_output)
 finally:wrapped.close()
class ProcessPreparationService(output.ProcessPreparationService):
 def __init__(self,rom,capacity,shared_output=True):
  if not shared_output:raise ValueError('Shared request candidate requires shared output')
  self.request_owner=SharedBlobOwner(64*1024*1024)
  try:self._initialize_request(rom,capacity,True)
  except BaseException:
   self.request_owner.close();raise
  self.connection=ParentConnection(self.connection,self.request_owner)
 def close(self):
  try:super().close()
  finally:
   if not self.process.is_alive():self.request_owner.close()
  self.shutdown_evidence.update(request_mapping_closed=self.request_owner.closed,request_acknowledged=self.connection.acknowledged,request_stage_totals=self.connection.stage_totals)
source=textwrap.dedent(inspect.getsource(base.ProcessPreparationService.__init__)).replace('def __init__(', 'def _initialize_request(',1).replace('target=_child','target=request_child').replace('args=(child,rom,shared_descriptor)','args=(child,rom,shared_descriptor,self.request_owner.memory.name)')
namespace=dict(base.ProcessPreparationService.__init__.__globals__,request_child=request_child)
exec(compile(source,'shared-request-service-init','exec'),namespace)
ProcessPreparationService._initialize_request=namespace['_initialize_request']
