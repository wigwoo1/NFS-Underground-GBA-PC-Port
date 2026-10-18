"""Bounded private storage preparation; no published frame ever returns here."""
import threading
from collections import deque
import _owned_frame_capture_prepared_candidate as native
class PreparedFrames:
 def __init__(self,capacity=2,frame_bytes=0x1000000):
  if not 1<=capacity<=2 or not 40<=frame_bytes<=0x1000000:raise ValueError('Invalid preparation bound')
  self.capacity=capacity;self.frame_bytes=frame_bytes;self.ready=deque();self.capture_lock=threading.Lock();self.cv=threading.Condition();self.closed=False;self.error=None;self.peak=0;self.created=0;self.taken=0
  self.thread=threading.Thread(target=self._run,name='Private frame preparation',daemon=False);self.thread.start()
 def _run(self):
  try:
   while True:
    with self.cv:
     self.cv.wait_for(lambda:self.closed or len(self.ready)<self.capacity)
     if self.closed:return
    capsule=native.prepare(self.frame_bytes)
    with self.cv:
     if self.closed:return
     self.ready.append(capsule);self.created+=1;self.peak=max(self.peak,len(self.ready));self.cv.notify_all()
  except BaseException as error:
   with self.cv:self.error=error;self.cv.notify_all()
 def capture(self,address,epoch,refresh):
  with self.capture_lock:return self._capture(address,epoch,refresh)
 def _capture(self,address,epoch,refresh):
  with self.cv:
   self.cv.wait_for(lambda:self.closed or self.error is not None or self.ready)
   if self.closed:raise RuntimeError('Preparation closed')
   if self.error is not None:raise RuntimeError('Preparation failed') from self.error
   capsule=self.ready.popleft();self.taken+=1;self.cv.notify_all()
  return native.capture(capsule,address,epoch,refresh)
 def close(self):
  with self.cv:self.closed=True;self.cv.notify_all()
  self.thread.join()
  with self.capture_lock:
   with self.cv:self.ready.clear()
  return dict(joined=not self.thread.is_alive(),pending=len(self.ready),created=self.created,taken=self.taken,peak=self.peak,capacity=self.capacity)
