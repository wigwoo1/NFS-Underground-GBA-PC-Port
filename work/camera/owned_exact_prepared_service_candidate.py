import threading
from collections import deque
import _owned_frame_capture_exact_candidate as native
import _owned_frame_capture_release_candidate as fallback
class ExactPreparedFrames:
 def __init__(self):
  self.cv=threading.Condition();self.capture_lock=threading.Lock();self.ready=deque();self.requested=None;self.closed=False;self.error=None;self.hits=0;self.misses=0;self.discarded=0;self.peak=0
  self.thread=threading.Thread(target=self._run,name='Exact private frame preparation',daemon=False);self.thread.start()
 def _run(self):
  try:
   while True:
    with self.cv:
     self.cv.wait_for(lambda:self.closed or (self.requested is not None and len(self.ready)<2))
     if self.closed:return
     size=self.requested
    capsule=native.prepare(size)
    with self.cv:
     if self.closed:return
     if size!=self.requested:self.discarded+=1;continue
     self.ready.append((size,capsule));self.peak=max(self.peak,len(self.ready));self.cv.notify_all()
  except BaseException as error:
   with self.cv:self.error=error;self.cv.notify_all()
 def capture(self,address,epoch,refresh):
  with self.capture_lock:
   with self.cv:
    if self.closed:raise RuntimeError('Preparation closed')
    if self.error is not None:raise RuntimeError('Preparation failed') from self.error
   size=native.frame_size(address,epoch,refresh)
   with self.cv:
    if self.closed:raise RuntimeError('Preparation closed')
    if self.error is not None:raise RuntimeError('Preparation failed') from self.error
    if self.requested!=size:
     self.discarded+=len(self.ready);self.ready.clear();self.requested=size
    capsule=self.ready.popleft()[1] if self.ready else None
    if capsule is None:self.misses+=1
    else:self.hits+=1
    self.cv.notify_all()
   return fallback.capture(address,epoch,refresh) if capsule is None else native.capture(capsule,address,epoch,refresh)
 def close(self):
  with self.cv:self.closed=True;self.cv.notify_all()
  self.thread.join()
  with self.capture_lock:
   with self.cv:self.ready.clear()
  return dict(joined=not self.thread.is_alive(),pending=len(self.ready),hits=self.hits,misses=self.misses,discarded=self.discarded,peak=self.peak,capacity=2)
