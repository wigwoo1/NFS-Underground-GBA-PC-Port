"""Bounded immutable HUD creation worker; explicit one-time creator transfer."""
import queue,threading
from concurrent.futures import Future
from owned_hud_shared_library_binding_candidate import HudFrameSnapshot
class HudPreparationService:
 def __init__(self,native_library,capacity=2,factory=HudFrameSnapshot):
  if not 1<=capacity<=2:raise ValueError('HUD service capacity must be one or two')
  self.library=native_library;self.factory=factory;self.capacity=capacity;self.lock=threading.Lock();self.close_lock=threading.Lock();self.pending=set();self.closed=False;self.jobs=queue.Queue(capacity+1);self.thread=threading.Thread(target=self._run,name='NFSUG HUD snapshot preparation');self.thread.start()
 def submit(self,base):
  if type(base) is not bytes:raise ValueError('Immutable frame required')
  with self.lock:
   if self.closed:raise RuntimeError('HUD preparation closed')
   if len(self.pending)>=self.capacity:raise RuntimeError('HUD preparation capacity exhausted')
   future=Future();self.pending.add(future);self.jobs.put_nowait((future,base));return future
 def _run(self):
  while True:
   job=self.jobs.get()
   if job is None:return
   future,base=job
   if not future.set_running_or_notify_cancel():continue
   try:snapshot=self.factory(base,native_library=self.library)
   except BaseException as error:future.set_exception(error)
   else:future.set_result(snapshot)
 def take(self,future,timeout=None):
  with self.lock:
   if self.closed or future not in self.pending:raise RuntimeError('HUD transfer unavailable')
  # Wait without holding service lock. Transfer is serialized against close.
  try:future.result(timeout)
  except BaseException:
   if future.done():
    with self.lock:self.pending.discard(future)
   raise
  with self.lock:
   if self.closed or future not in self.pending:raise RuntimeError('HUD transfer unavailable')
   snapshot=future.result();self.pending.remove(future);return snapshot
 def close(self):
  if threading.current_thread() is self.thread:raise RuntimeError('HUD service cannot close itself')
  with self.close_lock:
   with self.lock:
    if self.closed:return
    self.closed=True;self.jobs.put_nowait(None)
   self.thread.join()
   errors=[]
   for future in self.pending:
    if future.cancelled():continue
    try:snapshot=future.result()
    except BaseException:continue
    try:snapshot.close()
    except BaseException as error:errors.append(error)
   self.pending.clear();self.library=None;self.factory=None
   if errors:raise errors[0]
