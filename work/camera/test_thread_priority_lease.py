import threading
from owned_thread_priority import ThreadPriorityLease
results=[]
def run():
 for requested in (0,1):
  lease=ThreadPriorityLease(requested)
  try:raise ValueError('diagnostic body failed')
  except ValueError:pass
  finally:lease.close()
  assert lease.closed and lease.restored==lease.before
  lease.close();results.append(lease.evidence())
thread=threading.Thread(target=run);thread.start();thread.join();assert len(results)==2
for bad in (-1,2):
 try:ThreadPriorityLease(bad)
 except ValueError:pass
 else:raise AssertionError('Invalid priority accepted')
print('PASS real thread priority application/restoration, exception cleanup, idempotent close, bounds',results)
