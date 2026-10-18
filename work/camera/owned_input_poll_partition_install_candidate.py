"""Opt-in renderer input poll partition; bounded slow-call evidence."""
import inspect,textwrap,time,json,atexit,ctypes as C
import owned_native_source_segmented_release_worker_candidate as module
original=module.NativeSourceWorker._poll_input
rows=[];total=0;dropped=0
def observe(self,session,started,elapsed,stages):
 global total,dropped
 total+=1
 if elapsed>10000000:
  row=dict(begin_ns=started,end_ns=time.perf_counter_ns(),native_elapsed_ns=elapsed,stages_ns=list(stages),thread=self.input_poll_thread)
  if len(rows)<128:rows.append(row)
  else:dropped+=1
def poll(self,session):
 import threading
 assert threading.get_ident()==self.thread.ident
 state=(C.c_uint32*4)();elapsed=C.c_uint64();stages=(C.c_uint64*4)();started=time.perf_counter_ns()
 session.source.nf_owned_input_poll_timed.argtypes=[C.c_void_p]
 session.source.nf_owned_input_stages.argtypes=[C.c_void_p]
 if session.source.nf_owned_input_poll_timed(C.byref(elapsed))!=1:raise RuntimeError('Native timed input polling failed')
 if session.source.nf_owned_input_stages(stages)!=1:raise RuntimeError('Native input stage retrieval failed')
 if session.source.nf_owned_input_snapshot(state)!=1:raise RuntimeError('Native input snapshot failed')
 with self.input_lock:
  self.input_state=tuple(state);self.input_polls+=1;self.input_poll_thread=threading.get_ident()
 observe(self,session,started,elapsed.value,stages)
module.NativeSourceWorker._poll_input=poll
def save():
 from pathlib import Path
 out=Path('work/camera/prototype-runs')/('input-poll-partition-'+str(time.time_ns())+'.json')
 out.write_text(json.dumps(dict(total=total,dropped=dropped,rows=rows,stage_order=['window_messages','keyboard_focus','controller_snapshot','publish_input'],scope='Native timed input poll elapsed includes scheduling and message dispatch; no exclusive CPU attribution'),indent=2))
 print('INPUT_POLL_PARTITION',out,flush=True)
atexit.register(save)
