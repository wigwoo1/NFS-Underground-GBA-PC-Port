"""Read-only bounded parent process memory observer; no collector changes."""
import threading,time,json,runpy,sys,gc
from pathlib import Path
from collections import deque
from owned_process_memory_candidate import read
if __name__=='__main__':
 target=sys.argv.pop(1)
 if target not in ('run_native_serialized_traces_candidate.py','run_native_array_types_candidate.py'):raise ValueError('Unknown isolated runner')
 samples=deque(maxlen=256);errors=[];stop=threading.Event();before=list(gc.get_threshold());frozen=gc.get_freeze_count()
 def observe():
  while not stop.is_set():
   try:samples.append(dict(time_ns=time.perf_counter_ns(),**read()))
   except BaseException as e:errors.append(repr(e));return
   stop.wait(.5)
 thread=threading.Thread(target=observe,name='bounded-parent-memory-observer');thread.start()
 try:runpy.run_path(str(Path(__file__).with_name(target)),run_name='__main__')
 finally:
  stop.set();thread.join(5);assert not thread.is_alive()
  assert list(gc.get_threshold())==before and gc.get_freeze_count()==frozen
  path=Path('work/camera/prototype-runs')/('trace-memory-'+str(time.time_ns())+'.json')
  out=dict(target=target,samples=list(samples),errors=errors,capacity=256,interval_seconds=.5,thresholds_before=before,thresholds_after=list(gc.get_threshold()),frozen_before=frozen,frozen_after=gc.get_freeze_count(),observer_stopped=True,scope='Parent process private/working-set bytes includes startup and shutdown; extra observer thread may perturb scheduling. No child/GPU memory, forced collection or collector policy changes.')
  path.write_text(json.dumps(out,indent=2));print('TRACE_MEMORY',path,flush=True)
