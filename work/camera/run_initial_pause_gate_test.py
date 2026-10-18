"""Diagnostic-only first interval gate; never enabled by playable launchers."""
import runpy,sys,time
from live_native_batch_candidate import NativeBatchWorker
original=NativeBatchWorker._draw_intervals
def gated(self,*args,**kwargs):
 if not getattr(self,'initial_pause_gate_waiting',False):
  self.initial_pause_gate_waiting=True;deadline=time.perf_counter()+10
  while not self.paused:
   if time.perf_counter()>deadline:raise RuntimeError('Initial pause gate not acknowledged')
   time.sleep(.001)
  return False
 return original(self,*args,**kwargs)
NativeBatchWorker._draw_intervals=gated
if '--smoke-initial-pause' not in sys.argv:sys.argv.append('--smoke-initial-pause')
runpy.run_path('work/camera/run_process_transport_dedup_candidate.py',run_name='__main__')
