"""Opt-in renderer material-call execution accounting; graphics order unchanged."""
import ctypes as C
from ctypes import wintypes as W
import time,threading
from owned_uncovered_window_candidate import OwnedD3DConsumer
kernel=C.WinDLL('kernel32',use_last_error=True)
kernel.GetCurrentThread.restype=W.HANDLE
kernel.QueryThreadCycleTime.argtypes=[W.HANDLE,C.POINTER(C.c_uint64)]
kernel.GetThreadTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
def sample():
 h=kernel.GetCurrentThread();cycles=C.c_uint64();a,b,k,u=[W.FILETIME() for _ in range(4)]
 assert kernel.QueryThreadCycleTime(h,C.byref(cycles))
 assert kernel.GetThreadTimes(h,C.byref(a),C.byref(b),C.byref(k),C.byref(u))
 cpu=((k.dwHighDateTime<<32)|k.dwLowDateTime)+((u.dwHighDateTime<<32)|u.dwLowDateTime)
 return time.perf_counter_ns(),cycles.value,cpu*100
namespace=OwnedD3DConsumer.render.__globals__;original=namespace['profiled']
observer=None
def measured(self,name,args):
 before=sample();result=original(self,name,args);after=sample()
 row=self.d3d_call_profiles[-1];assert row['call']==name
 assert before[0]<=row['caller_begin_ns']<=row['caller_end_ns']<=after[0]
 row['caller_execution']=dict(thread=threading.get_ident(),before=list(before),after=list(after),raw_cycles=after[1]-before[1],cpu_ns=after[2]-before[2],scope='Includes execution getter overhead and foreign-call entry/return; CPU accounting coarse, cycles not elapsed-time conversion.')
 if observer is not None:observer(self,row)
 return result
namespace['profiled']=measured
