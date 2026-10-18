"""Actual spawned wrong acknowledgement through the owned preparation pipeline."""
import json,types
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
from owned_shared_request_service_candidate import ProcessPreparationService

def wrong_ack_child(connection,rom,output_descriptor,request_name):
 input_memory=SharedMemory(name=request_name);output_memory=SharedMemory(name=output_descriptor[0])
 try:
  value=connection.recv();assert value[0]=='request_shared';descriptor=value[1]
  connection.send(('request_ack',(descriptor[0],descriptor[1],descriptor[2]+1,descriptor[3])))
  assert connection.recv() is None
 finally:input_memory.close();output_memory.close();connection.close()
class WrongAckService(ProcessPreparationService):pass
original=ProcessPreparationService._initialize_request
namespace=dict(original.__globals__,request_child=wrong_ack_child)
WrongAckService._initialize_request=types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
if __name__=='__main__':
 service=WrongAckService(b'isolated-transport-test',2)
 request=(0,None,(1,2),(b'frame',b'graph',b'supplement',None,None),(.25,))
 checks=[]
 try:
  future=service.pipeline.submit(lambda:service.connection.send(request),timeout=5)
  try:service.take(future)
  except RuntimeError as error:assert 'acknowledgement mismatch' in str(error);checks.append('wrong_ack_propagated_through_future')
  else:raise AssertionError('Wrong ack accepted')
  assert service.connection.failed and service.connection.acknowledged==0
  try:service.connection.send(request)
  except RuntimeError:checks.append('failed_mapping_reuse_rejected')
  else:raise AssertionError('Failed mapping reused')
 finally:service.close()
 assert not service.process.is_alive() and not service.pipeline.thread.is_alive()
 assert service.shutdown_evidence['child_exitcode']==0 and service.shutdown_evidence['forced_termination'] is False and service.request_owner.closed and service.shared_owner.closed and service.connection.closed
 for name in (service.request_owner.memory.name,service.shared_owner.memory.name):
  try:memory=SharedMemory(name=name)
  except FileNotFoundError:checks.append('mapping_no_longer_openable')
  else:memory.close();raise AssertionError('Closed mapping remains openable')
 out=dict(result='PASS_ACTUAL_SPAWNED_SHARED_REQUEST_ACK_FAILURE',checks=checks,shutdown=service.shutdown_evidence,scope='Real spawned wrong serial ack with graceful child shutdown and future failure. No actual blocked child/30s timeout, game images or live timing claim.')
 Path('work/camera/prototype-runs/spawned-request-ack-failure-20261009.json').write_text(json.dumps(out,indent=2));print(out)
