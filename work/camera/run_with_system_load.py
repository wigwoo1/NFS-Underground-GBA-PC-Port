"""Opt-in system CPU observations alongside the unchanged prototype entry point."""
import ctypes as C,json,runpy,sys,threading,time
from pathlib import Path

def busy_fraction(previous,current):
 delta=[b-a for a,b in zip(previous,current)]
 if min(delta)<0:raise ValueError('System counters moved backwards')
 total=delta[1]+delta[2]
 if total<=0:return None
 if delta[0]>total:raise ValueError('Idle exceeds total')
 return (total-delta[0])/total

def run():
 source=Path(sys.argv[1]);sys.argv=sys.argv[1:]
 kernel=C.WinDLL('kernel32',use_last_error=True)
 query=kernel.GetSystemTimes;query.argtypes=[C.POINTER(C.c_uint64)]*3;query.restype=C.c_int
 stop=threading.Event();rows=[];errors=[]
 def sample():
  previous=None;previous_ns=None
  while not stop.is_set():
   begin=time.perf_counter_ns();values=[C.c_uint64() for _ in range(3)]
   if not query(*(C.byref(v) for v in values)):
    errors.append(dict(error=C.get_last_error(),begin_ns=begin));return
   end=time.perf_counter_ns();current=[v.value for v in values]
   if previous is not None:
    rows.append(dict(begin_ns=previous_ns,end_ns=end,query_begin_ns=begin,query_end_ns=end,busy_fraction=busy_fraction(previous,current),counters=current))
   previous=current;previous_ns=end;stop.wait(.25)
 output=Path('work/camera/prototype-runs')/('system-load-'+str(time.time_ns())+'.json')
 worker=threading.Thread(target=sample,name='diagnostic-system-load',daemon=True);worker.start()
 try:runpy.run_path(str(source),run_name='__main__')
 finally:
  stop.set();worker.join(2)
  output.write_text(json.dumps(dict(source=str(source),samples=rows,errors=errors,thread_stopped=not worker.is_alive(),scope='GetSystemTimes aggregate CPU busy fraction over timestamped intervals; kernel includes idle. Not process attribution, GPU utilization, scheduling causality or scanout evidence. Diagnostic thread adds measurement overhead.'),indent=2));print(output)
  if worker.is_alive() or errors:raise RuntimeError('System load diagnostic failed')
if __name__=='__main__':run()
