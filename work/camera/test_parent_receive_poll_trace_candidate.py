from owned_progressive_parent_service_candidate import ProgressiveService
class Connection:
 def __init__(self,ready=True):self.ready=ready;self.reads=0
 def poll(self,timeout):return self.ready
 def recv(self):self.reads+=1;return ('sample',3,0)
for enabled in (False,True):
 service=object.__new__(ProgressiveService);service.receive_poll_trace=enabled;service.last_receive_poll=None;service.connection=Connection()
 assert service._receive(.01)==('sample',3,0) and service.connection.reads==1
 if enabled:
  stamps=list(service.last_receive_poll.values());assert stamps==sorted(stamps)
 else:assert service.last_receive_poll is None
 service.connection=Connection(False)
 try:service._receive(.01)
 except TimeoutError:pass
 else:raise AssertionError('Missing timeout')
 assert service.connection.reads==0
 for timeout in (-1,31,float('nan')):
  try:service._receive(timeout)
  except ValueError:pass
  else:raise AssertionError('Invalid wait accepted')
print('PASS_PARENT_RECEIVE_POLL_TRACE_VALUES_TIMEOUTS_GUARDS')
