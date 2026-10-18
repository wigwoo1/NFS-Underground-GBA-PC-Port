import queue,threading,json
from owned_notification_queue import NativeNotificationQueue
q=NativeNotificationQueue(2)
try:
 try:q.get(timeout=0)
 except queue.Empty:pass
 else:raise AssertionError('Empty queue accepted')
 q.put((11,),timeout=0);q.put((12,),timeout=0)
 try:q.put((13,),timeout=0)
 except queue.Full:pass
 else:raise AssertionError('Capacity exceeded')
 assert q.get(timeout=0)==(11,) and q.get(timeout=0)==(12,)
 observed=[]
 def consumer():
  for _ in range(100):
   observed.append(q.get(timeout=2)[0]);assert q.last_get[0]<=q.last_get[1]<=q.last_get[2]
 worker=threading.Thread(target=consumer);worker.start()
 try:
  for i in range(1,101):q.put((i,),timeout=2)
 finally:worker.join(3)
 assert not worker.is_alive() and observed==list(range(1,101))
 q.put(0,timeout=0);assert q.get(timeout=0)==0
finally:q.close()
assert q.owner is None;q.close()
print(json.dumps(dict(result='PASS',checks=['empty','full','FIFO','100 threaded identities','ordered native timestamps','quit sentinel','joined shutdown','idempotent close'])))
