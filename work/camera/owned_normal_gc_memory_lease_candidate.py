import gc,threading,time
from collections import deque
from owned_process_memory_candidate import read as process_memory
class StartupGCScanLease:
 def __init__(self):self.owner=threading.get_ident();self.active=False;self.evidence={}
 def enter(self):
  if threading.get_ident()!=self.owner or self.active:raise RuntimeError('GC interval lease owner or state mismatch')
  self.previous=gc.get_threshold();self.frozen=gc.get_freeze_count();begin=time.perf_counter_ns();collected=gc.collect();gc.set_threshold(*self.previous);self.active=True
  self.evidence=dict(mode='normal_threshold_memory_control',previous_thresholds=list(self.previous),candidate_thresholds=list(gc.get_threshold()),startup_collected=collected,startup_scan_ns=time.perf_counter_ns()-begin,preexisting_frozen_objects=self.frozen,automatic_gc_enabled=gc.isenabled(),restored=False)
  self.stop=threading.Event();self.samples=deque(maxlen=256);self.memory_errors=[]
  def sample():
   while not self.stop.is_set():
    try:self.samples.append(dict(time_ns=time.perf_counter_ns(),**process_memory()))
    except BaseException as error:self.memory_errors.append(str(error));return
    self.stop.wait(.5)
  self.sampler=threading.Thread(target=sample,name="GC candidate memory observer");self.sampler.start()
 def close(self):
  if threading.get_ident()!=self.owner:raise RuntimeError('GC interval lease owner mismatch')
  if not self.active:return
  self.stop.set();self.sampler.join(timeout=5)
  if self.sampler.is_alive():raise RuntimeError("Memory observer failed to stop")
  gc.set_threshold(*self.previous);self.active=False;self.evidence.update(restored=True,restored_thresholds=list(gc.get_threshold()),remaining_frozen_objects=gc.get_freeze_count())

  before=process_memory();begin=time.perf_counter_ns();collected=gc.collect();self.evidence.update(memory_samples=list(self.samples),memory_errors=self.memory_errors,memory_before_final_collection=before,memory_after_final_collection=process_memory(),final_collected=collected,final_collection_ns=time.perf_counter_ns()-begin,sampler_stopped=True)
