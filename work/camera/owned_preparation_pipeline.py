"""Bounded CPU preparation ownership, independent of the GPU context thread."""
import threading,queue,time,math
from concurrent.futures import Future,CancelledError
class PreparationPipeline:
 def __init__(self,capacity=2):
  if not 1<=capacity<=10:raise ValueError('Invalid preparation capacity')
  self.lock=threading.Lock();self.space=threading.BoundedSemaphore(capacity);self.jobs=queue.Queue();self.generation=0;self.closed=False;self.ready={};self.timings=[]
  self.thread=threading.Thread(target=self._run,name='owned-scene-preparation',daemon=True);self.thread.start()
 def submit(self,factory,timeout=0,abort=None,identity=None):
  submitted_ns=time.perf_counter_ns()
  if not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Invalid preparation wait timeout')
  deadline=time.monotonic()+timeout
  while True:
   with self.lock:
    if self.closed:raise ValueError('Preparation pipeline closed')
   if abort is not None and abort():raise RuntimeError('Preparation submission cancelled')
   if self.space.acquire(blocking=False):break
   if not timeout:raise ValueError('Preparation capacity exhausted')
   remaining=deadline-time.monotonic()
   if remaining<=0:raise RuntimeError('Preparation queue stalled')
   if self.space.acquire(timeout=min(.05,remaining)):break
  with self.lock:
   if self.closed:self.space.release();raise ValueError('Preparation pipeline closed')
   future=Future();future._owned_preparation_generation=self.generation
   timing=dict(identity=identity,generation=self.generation,submitted_ns=submitted_ns,enqueued_ns=time.perf_counter_ns(),dequeued_ns=None,validated_ns=None,finalized_ns=None,started_ns=None,finished_ns=None,published_ns=None,taken_ns=None,status="queued")
   future._owned_preparation_timing=timing
   if len(self.timings)<10000:self.timings.append(timing)
   self.jobs.put((self.generation,factory,future));return future
 def _run(self):
  while True:
   job=self.jobs.get()
   if job is None:return
   generation,factory,future=job
   timing=future._owned_preparation_timing
   timing["dequeued_ns"]=time.perf_counter_ns()
   try:
    with self.lock:valid=not self.closed and generation==self.generation
    timing["validated_ns"]=time.perf_counter_ns()
    if not valid:timing.update(status="cancelled_before_start",finished_ns=time.perf_counter_ns());future.cancel();self.space.release();continue
    timing.update(started_ns=time.perf_counter_ns(),status="running")
    result=factory()
    timing["finished_ns"]=time.perf_counter_ns()
    with self.lock:
     if self.closed or generation!=self.generation:
      result.close();timing["status"]="retired_after_prepare";future.cancel();self.space.release()
     else:
      self.ready[future]=result;timing.update(status="ready",published_ns=time.perf_counter_ns());future.set_result(result)
   except BaseException as error:
    timing.update(status="failed",finished_ns=time.perf_counter_ns());future.set_exception(error);self.space.release()
   finally:
    timing["finalized_ns"]=time.perf_counter_ns()
 def take(self,future,timeout=30):
  result=future.result(timeout)
  with self.lock:
   if getattr(future,'_owned_preparation_generation',None)!=self.generation or self.closed:raise CancelledError('Prepared result retired by lifecycle change')
   if self.ready.pop(future,None) is not result:raise ValueError('Prepared result invalidated or already taken')
   future._owned_preparation_timing.update(status="taken",taken_ns=time.perf_counter_ns());self.space.release();return result
 def invalidate(self):
  with self.lock:
   self.generation+=1
   for future,result in self.ready.items():result.close();future._owned_preparation_timing["status"]="retired_ready";self.space.release()
   self.ready.clear()
 def close(self):
  with self.lock:
   if self.closed:return
   self.closed=True
  self.invalidate();self.jobs.put(None);self.thread.join(30)
  if self.thread.is_alive():raise RuntimeError('Preparation shutdown stalled')
