"""Optional native boundary measurements; identical original batch implementation."""
import ctypes as C,time
from pathlib import Path
import owned_wall_visibility_candidate as target
lib=C.CDLL(str(Path(__file__).with_name('wall-visibility-timed.dll').resolve()))
fn=lib.nf_wall_visibility_timed;fn.argtypes=target.helper().nf_wall_visibility_batch.argtypes+[C.POINTER(C.c_uint64)]
held_lib=C.PyDLL(str(Path(__file__).with_name('wall-visibility-timed.dll').resolve()))
held_fn=held_lib.nf_wall_visibility_timed;held_fn.argtypes=fn.argtypes
held_small_enabled=False
records=[];dropped=0
class TimedHelper:
 def nf_wall_visibility_batch(self,*args):
  global dropped
  trace=(C.c_uint64*4)();begin=time.perf_counter_ns();held=held_small_enabled and args[1]<=64
  result=(held_fn if held else fn)(*args,trace);end=time.perf_counter_ns()
  row=dict(held_small=held,started_ns=begin,completed_ns=end,count=args[1],wrapper_ns=end-begin,native_ns=(trace[1]-trace[0])*1000000000/trace[2],native_cycles=trace[3],result=result)
  if len(records)<20000:records.append(row)
  else:dropped+=1
  return result
helper=TimedHelper()
def install():target.helper=lambda:helper
