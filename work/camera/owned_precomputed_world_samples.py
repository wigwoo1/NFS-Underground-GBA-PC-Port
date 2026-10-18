"""Bounded complete presentation samples prepared before GPU consumption."""
import ctypes,math,time
from owned_thread_cycles import read as thread_cycles
class PrecomputedWorldSamples:
 def __init__(self,prepared,alphas,budget=64*1024*1024,trace=False):
  self.samples={};self.bytes=0;self.sample_timings=[];self.prepared_close_ns=None
  try:
   if not 1<=len(alphas)<=8:raise ValueError('Unbounded world sample count')
   for alpha in alphas:
    if not math.isfinite(alpha) or not 0<=alpha<=1 or alpha in self.samples:raise ValueError('Invalid world sample identity')
    if trace:started=time.perf_counter_ns();cpu_started=time.thread_time_ns();cycles_started=thread_cycles()
    result=prepared.sample(alpha)
    if trace:
     completed=time.perf_counter_ns();cpu_completed=time.thread_time_ns();cycles_completed=thread_cycles()
     self.sample_timings.append(dict(assembly_stages=getattr(prepared.pair,'_last_sample_stages',[]),alpha=alpha,started_ns=started,completed_ns=completed,wall_ns=completed-started,thread_cycles=cycles_completed-cycles_started,thread_cpu_ns=cpu_completed-cpu_started))
    self.bytes+=len(result[0])+sum(ctypes.sizeof(x) for x in result[1:4] if x is not None)
    if self.bytes>budget:raise ValueError('Prepared world sample budget exceeded')
    self.samples[alpha]=result
  except BaseException:self.close();raise
  finally:
   if trace:close_started=time.perf_counter_ns()
   prepared.close()
   if trace:self.prepared_close_ns=time.perf_counter_ns()-close_started
 def sample(self,alpha):
  if alpha not in self.samples:raise ValueError('Unprepared world presentation sample')
  return self.samples[alpha]
 def close(self):self.samples.clear();self.bytes=0
