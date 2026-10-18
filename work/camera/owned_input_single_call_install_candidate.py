"""Diagnostic single crossing; unchanged native fresh poll/stages/snapshot."""
import ctypes as C,time,threading
from pathlib import Path
import owned_progressive_input_poll_trace_candidate as trace
bridge=C.CDLL(str(Path('work/camera/owned-input-single-call-candidate.dll').resolve()))
bridge.nf_input_poll_snapshot_timed.argtypes=[C.c_void_p]*4+[C.c_size_t,C.c_void_p,C.c_size_t]
def poll(self,session):
 assert threading.get_ident()==self.thread.ident
 if not hasattr(self,'input_bridge_binding'):
  self.input_bridge_binding=(session.source,*(C.cast(getattr(session.source,name),C.c_void_p) for name in ('nf_owned_input_poll_timed','nf_owned_input_stages','nf_owned_input_snapshot')))
 library,one,two,three=self.input_bridge_binding;assert library is session.source
 timing=(C.c_uint64*5)();state=(C.c_uint32*4)();begin=time.perf_counter_ns()
 status=bridge.nf_input_poll_snapshot_timed(one,two,three,timing,C.sizeof(timing),state,C.sizeof(state))
 end=time.perf_counter_ns()
 if status!=1:raise RuntimeError('Native input bridge failed: '+str(status))
 with self.input_lock:
  self.input_state=tuple(state);self.input_polls+=1;self.input_poll_thread=threading.get_ident()
 self.last_input_poll_profile=dict(input_bridge=True,begin_ns=begin,end_ns=end,native_ns=timing[0],message_ns=timing[1],keyboard_ns=timing[2],controller_ns=timing[3],publication_ns=timing[4],connected=state[3],poll_number=self.input_polls)
trace.worker._poll_input=poll
