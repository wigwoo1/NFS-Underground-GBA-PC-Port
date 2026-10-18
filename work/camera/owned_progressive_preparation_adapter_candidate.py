"""Sequential progressive adapter; first sample fulfills the renderer-shaped future."""
import threading,queue,weakref,time,math
from concurrent.futures import Future,CancelledError
from owned_progressive_parent_service_candidate import ProgressiveService
from owned_progressive_pair_candidate import ProgressivePair
class HistoryOnlyPair:
 history_only=True
 def __init__(self):
  self.alphas=();self.first=Future();self.cv=threading.Condition();self.closed=False
 def finish(self):
  if not self.closed:self.first.set_result(self)
 def fail(self,error):
  if not self.first.done():self.first.set_exception(error)
 def close(self):
  with self.cv:
   self.closed=True
   if not self.first.done():self.first.cancel()
 def sample(self,alpha):raise ValueError('History-only interval has no display sample')
class ProgressivePreparationAdapter:
 supports_pending_replay=True
 def __init__(self,rom,capacity=2,shared_output=False):

  if type(capacity) is not int or not 1<=capacity<=8:raise ValueError('Invalid request capacity')
  self.service=ProgressiveService(rom,shared_output=shared_output);self.capacity=capacity;self.space=threading.BoundedSemaphore(capacity);self.jobs=queue.Queue();self.lock=threading.Lock();self.generation=0;self.closed=False;self.pairs=weakref.WeakSet();self.errors=[];self.completed=0
  self.protocol="progressive-shared-input-output-private-copy" if shared_output else "progressive-private-packets"
  self.stage_samples=[];self.profiles=[];self.cache_diagnostics=[];self.profile_refresh=None;self.cache_diagnostic_range=None;self.diagnostic_dropped=0
  self.thread=threading.Thread(target=self._run,name='progressive-preparation',daemon=True);self.thread.start()
 def warm_start(self,frame,scene):
  with self.lock:
   if self.closed or self.completed or self.pairs or getattr(self,'startup_requested',False):raise ValueError('Startup requires unused adapter')
   self.startup_requested=True;future=Future();self.jobs.put(('warm',(frame,scene),future))
  return future.result(30)
 def submit(self,older,newer,alphas=None,timeout=0,abort=None):
  if not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Invalid submission timeout')
  submission_begin_ns=time.perf_counter_ns()
  pair=HistoryOnlyPair() if alphas is not None and not tuple(alphas) else ProgressivePair(alphas)
  deadline=time.monotonic()+timeout
  while not self.space.acquire(blocking=False):
   if abort is not None and abort():raise CancelledError('Submission cancelled')
   with self.lock:
    if self.closed:raise ValueError('Adapter closed')
   remaining=deadline-time.monotonic()
   if remaining<=0:raise TimeoutError('Request capacity exhausted')
   if self.space.acquire(timeout=min(.05,remaining)):break
  with self.lock:
   if self.closed:self.space.release();raise ValueError('Adapter closed')
   future=pair.first;future._progressive_generation=self.generation;future._progressive_taken=False;self.pairs.add(pair);pair.submission_begin_ns=submission_begin_ns;pair.enqueued_ns=time.perf_counter_ns();self.jobs.put((self.generation,older,newer,pair));return future
 def _valid(self,generation):
  with self.lock:return not self.closed and generation==self.generation
 def _run(self):
  try:
   while True:
    job=self.jobs.get()
    if job is None:break
    if job[0]=='warm':
     _,source,future=job
     try:future.set_result(self.service.warm_start(*source))
     except BaseException as e:future.set_exception(e)
     continue
    generation,older,newer,pair=job;started=time.perf_counter_ns();sample_rows=[]
    try:
     if not self._valid(generation):pair.close();continue
     if self.service.generation!=generation:
      self.service.invalidate();self.service.generation=generation
     self.service.start(older,newer,pair.alphas)
     for _ in pair.alphas:
      while True:
       if not self._valid(generation) or pair.closed:raise CancelledError('Request retired')
       try:token,packet=self.service.take(.05);break
       except TimeoutError:continue
      if not self._valid(generation):raise CancelledError('Request retired')
      publication_begin=time.perf_counter_ns();pair.publish(packet);published=time.perf_counter_ns();self.service.acknowledge(token)
      sample_rows.append(dict(self.service.last_sample_timing,publication_begin_ns=publication_begin,published_ns=published,ack_sent_ns=time.perf_counter_ns()))
     self.service.finish()
     with pair.cv:
      if not pair.closed:pair.finish()
     self.completed+=1
     row=dict(protocol=self.protocol,generation=generation,older=older[1].graph.refresh,newer=newer[1].graph.refresh,prepared_sample_count=len(pair.alphas),history_only=not bool(pair.alphas),submission_begin_ns=pair.submission_begin_ns,enqueued_ns=pair.enqueued_ns,queue_wait_ns=started-pair.enqueued_ns,capacity_wait_ns=pair.enqueued_ns-pair.submission_begin_ns,started_ns=started,completed_ns=time.perf_counter_ns(),terminal=self.service.last_terminal,parent_start_timing=self.service.last_start_timing,parent_sample_rows=sample_rows)
     if len(self.stage_samples)<1000:self.stage_samples.append(row)
     else:self.diagnostic_dropped+=1
    except CancelledError:
     pair.close()
     if self.service.active:self.service.invalidate()
    except BaseException as e:
     pair.fail(e);self.errors.append(repr(e))
     if self.service.active:self.service.invalidate()
    finally:
     self.space.release();job=pair=older=newer=None
  finally:self.service.close()
 def take(self,future,timeout=30):
  pair=future.result(timeout)
  with self.lock:
   if self.closed or future._progressive_generation!=self.generation:raise CancelledError('Future retired')
   if future._progressive_taken:raise ValueError('Future already taken')
   future._progressive_taken=True
  return pair
 def invalidate(self):
  with self.lock:self.generation+=1;pairs=list(self.pairs)
  for pair in pairs:pair.close()
 def close(self):
  with self.lock:
   if self.closed:return
   self.closed=True
  self.invalidate();self.jobs.put(None);self.thread.join(20)
  if self.thread.is_alive():raise RuntimeError('Adapter shutdown pending')
  self.shutdown_evidence=dict(protocol=self.protocol,preparation_thread_alive=self.thread.is_alive(),child_alive=self.service.process.is_alive(),child_exitcode=self.service.process.exitcode,completed=self.completed,errors=list(self.errors),diagnostic_dropped=self.diagnostic_dropped)
