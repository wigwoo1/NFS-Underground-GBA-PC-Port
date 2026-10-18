"""Isolated live-worker integration of bounded request-authorized copies."""
import inspect,textwrap,ctypes as C,time,threading,queue
from live_owned_gpu_worker import LiveOwnedGPUWorker as Worker
from owned_handoff_copy_service_candidate import HandoffCopyService
from owned_handoff_copy_settlement_candidate import CopySettlement
original_init=Worker.__init__;original_pause=Worker.set_paused;original_close=Worker.close

def init(self,*args,**kwargs):
 original_init(self,*args,**kwargs)
 self.copy_service=HandoffCopyService(self.d,self.owner,self.capacity)
 self.copy_counts=dict(admitted=0,published=0,retired=0,failed=0);self.copy_count_lock=threading.Lock()
def pause(self,paused):
 if paused and not self.paused:
  with self.presentation_publication_lock:
   self.d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint]
   assert self.d.nf_owned_handoff_pause(self.owner,1)
  if not self.copy_service.wait_idle(30):raise RuntimeError('Copy retirement drain timed out')
 return original_pause(self,paused)
def close(self):
 if not self.copy_service.wait_idle(30):raise RuntimeError('Copy shutdown drain timed out')
 self.copy_service.close();self.copy_shutdown=dict(thread_alive=self.copy_service.thread.is_alive(),pending=self.copy_service.pending,counts=dict(self.copy_counts))
 return original_close(self)

method=Worker.submit;source=textwrap.dedent(inspect.getsource(method));marker=' # Publish paired preparation before making the native frame consumable.';assert source.count(marker)==1
source=source[:source.index(marker)]+''' # Pair and immutable snapshot are registered before background copy admission.
 if type(owned_frame) is not bytes or used!=len(owned_frame):
  self.space.release();raise ValueError('Async copy requires exact immutable full-scene frame')
 try:future=self.copy_service.submit(owned_frame)
 except BaseException:self.space.release();raise
 with self.copy_count_lock:self.copy_counts['admitted']+=1
 def notify(receipt):
  signal=(time.perf_counter_ns(),)
  limit=time.perf_counter()+30
  while True:
   if self.errors or not self.thread.is_alive():raise RuntimeError('Consumer unavailable for copy notification')
   try:self.signals.put(signal,timeout=.05);break
   except queue.Full:
    if time.perf_counter()>=limit:raise RuntimeError('Copy notification capacity stalled')
  with self.copy_count_lock:self.copy_counts['published']+=1
 def release():
  self.space.release()
  with self.copy_count_lock:self.copy_counts['retired']+=1
 def retire():
  self.d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint]
  if not self.d.nf_owned_handoff_pause(self.owner,1):raise RuntimeError('Failed copy publication retirement')
 def fail(errors):
  with self.copy_count_lock:self.copy_counts['failed']+=1
  self.errors.append('Async copy settlement: '+repr(errors))
 future.add_done_callback(CopySettlement(notify,release,retire,fail))
 submit_stages['async_copy_admitted']=True;submit_stages['submit_end_ns']=time.perf_counter_ns()
 if not hasattr(self,'submit_stage_samples'):self.submit_stage_samples=[]
 if len(self.submit_stage_samples)<10000:self.submit_stage_samples.append(submit_stages)
'''
namespace=dict(method.__globals__,CopySettlement=CopySettlement)
exec(compile(source,'async-copy-worker-submit','exec'),namespace)
Worker.submit=namespace['submit'];Worker.__init__=init;Worker.set_paused=pause;Worker.close=close
# The native renderer has its own close implementation; wrap that override too.
from live_native_hud_prefetch_generation_candidate import NativeLiveWorker
# An existing error must not suppress the consumer shutdown notification.
close_source=textwrap.dedent(inspect.getsource(NativeLiveWorker.close))
assert close_source.count('while self.thread.is_alive() and not self.errors:')==1
close_source=close_source.replace('while self.thread.is_alive() and not self.errors:','while self.thread.is_alive():')
close_namespace=dict(NativeLiveWorker.close.__globals__)
exec(compile(close_source,'async-native-error-shutdown','exec'),close_namespace)
original_native_close=close_namespace['close']
def native_close(self):
 if self.owner is None:return
 if not self.copy_service.wait_idle(30):raise RuntimeError('Native copy shutdown drain timed out')
 self.copy_service.close();self.copy_shutdown=dict(thread_alive=self.copy_service.thread.is_alive(),pending=self.copy_service.pending,counts=dict(self.copy_counts))
 return original_native_close(self)
NativeLiveWorker.close=native_close

