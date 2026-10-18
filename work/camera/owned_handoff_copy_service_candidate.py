"""Bounded single-thread native copy service; owner outlives close/join."""
import ctypes as C,queue,threading,struct,time
from concurrent.futures import Future
class HandoffCopyService:
 def __init__(self,dll,owner,capacity=2):
  if not owner or not 1<=capacity<=8:raise ValueError('Invalid owner/capacity')
  self.dll=dll;self.owner=owner;self.capacity=capacity;self.pending=0;self.closed=False
  self.lock=threading.Lock();self.idle=threading.Condition(self.lock);self.close_lock=threading.Lock();self.jobs=queue.Queue(capacity+1)
  dll.nf_owned_handoff_request_generation.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p];dll.nf_owned_handoff_request_generation.restype=C.c_int
  dll.nf_owned_handoff_push_authority.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_uint64,C.c_uint64,C.c_void_p];dll.nf_owned_handoff_push_authority.restype=C.c_int
  self.thread=threading.Thread(target=self._run,name='owned-handoff-copy');self.thread.start()
 def submit(self,frame):
  if type(frame) is not bytes or not 40<=len(frame)<=0x1000000:raise ValueError('Complete immutable frame required')
  epoch=struct.unpack_from('<Q',frame,24)[0];generation=C.c_uint64()
  with self.lock:
   if self.closed:raise RuntimeError('Copy service closed')
   if self.pending>=self.capacity:raise RuntimeError('Copy service capacity exhausted')
   if not self.dll.nf_owned_handoff_request_generation(self.owner,epoch,C.byref(generation)):raise RuntimeError('Request authority unavailable')
   future=Future();self.pending+=1;self.jobs.put_nowait((frame,epoch,generation.value,future));return future
 def _run(self):
  while True:
   job=self.jobs.get()
   if job is None:return
   frame,epoch,generation,future=job
   try:
    with self.lock:closed=self.closed
    if future.set_running_or_notify_cancel():
     if closed:raise RuntimeError('Copy service retired queued request')
     timing=(C.c_uint64*8)();ok=self.dll.nf_owned_handoff_push_authority(self.owner,frame,len(frame),epoch,generation,timing)
     future.set_result(dict(published=bool(ok),epoch=epoch,generation=generation,native_timing=list(timing)))
   except BaseException as exc:
    if not future.done():future.set_exception(exc)
   finally:
    frame=job=future=None
    with self.idle:self.pending-=1;self.idle.notify_all()
 def wait_idle(self,timeout=30):
  if threading.current_thread() is self.thread:raise RuntimeError('Cannot wait on copy thread')
  if timeout<0:raise ValueError('Nonnegative timeout required')
  deadline=time.monotonic()+timeout
  with self.idle:
   while self.pending:
    remaining=deadline-time.monotonic()
    if remaining<=0:return False
    self.idle.wait(remaining)
   return True
 def close(self):
  if threading.current_thread() is self.thread:raise RuntimeError('Cannot close from copy thread')
  with self.close_lock:
   with self.lock:
    if not self.closed:self.closed=True;self.jobs.put_nowait(None)
   self.thread.join()
   assert self.pending==0



