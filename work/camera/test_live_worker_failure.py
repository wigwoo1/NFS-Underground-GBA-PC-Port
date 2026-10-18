import threading,time,queue
from live_owned_gpu_worker import LiveOwnedGPUWorker
class Native:
 def __init__(self):self.destroyed=0
 def nf_owned_handoff_destroy(self,owner):self.destroyed+=1
worker=object.__new__(LiveOwnedGPUWorker);worker.preparation_service=None;worker.producer=threading.get_ident();worker.errors=[];worker.space=threading.Semaphore(0);worker.signals=queue.Queue(maxsize=1);worker.signals.put(('queued',));worker.owner=object();worker.d=Native();worker.scene_snapshot_lock=threading.Lock();worker.scene_snapshots={1:'retained'}
def fail():time.sleep(.05);worker.errors.append("ValueError('source failure')")
worker.thread=threading.Thread(target=fail);worker.thread.start();began=time.perf_counter()
try:worker.submit(b'frame')
except RuntimeError as e:assert 'source failure' in str(e)
else:raise AssertionError('Failure not propagated')
assert time.perf_counter()-began<1
try:worker.close()
except RuntimeError as e:assert 'source failure' in str(e)
else:raise AssertionError('Close failure lost')
assert worker.owner is None and worker.d.destroyed==1 and not worker.scene_snapshots
worker.close();assert worker.d.destroyed==1
print('PASS dead consumer/full queue failure propagation under1s; native ownership and snapshots released once')

