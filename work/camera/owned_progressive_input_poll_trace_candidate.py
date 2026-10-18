"""Observe unchanged fresh controller polling on its original owner thread."""
import ctypes as C,time,threading
import owned_native_transaction_worker_install_candidate as tx
import owned_native_source_segmented_release_worker_candidate as module
worker=module.NativeSourceWorker

def poll(self,session):
 assert threading.get_ident()==self.thread.ident
 elapsed=C.c_uint64();stages=(C.c_uint64*4)();state=(C.c_uint32*4)()
 session.source.nf_owned_input_poll_timed.argtypes=[C.c_void_p]
 session.source.nf_owned_input_stages.argtypes=[C.c_void_p]
 begin=time.perf_counter_ns()
 if session.source.nf_owned_input_poll_timed(C.byref(elapsed))!=1:raise RuntimeError('Native input polling failed')
 if session.source.nf_owned_input_stages(stages)!=1:raise RuntimeError('Native input stages unavailable')
 if session.source.nf_owned_input_snapshot(state)!=1:raise RuntimeError('Native input snapshot failed')
 end=time.perf_counter_ns()
 with self.input_lock:
  self.input_state=tuple(state);self.input_polls+=1;self.input_poll_thread=threading.get_ident()
 self.last_input_poll_profile=dict(begin_ns=begin,end_ns=end,native_ns=elapsed.value,message_ns=stages[0],keyboard_ns=stages[1],controller_ns=stages[2],publication_ns=stages[3],connected=state[3],poll_number=self.input_polls)
worker._poll_input=poll
source=tx.source;needle='thread=threading.get_ident(),previous_job_completed_ns='
assert source.count(needle)==1
source=source.replace(needle,'thread=threading.get_ident(),input_poll_profile=getattr(self,"last_input_poll_profile",None),previous_job_completed_ns=')
selected_session=worker._run.__globals__['NativeSourceSession']
namespace=dict(worker._run.__globals__);exec(compile(source,'native-owner-input-stage-trace','exec'),namespace)
namespace['NativeSourceSession']=selected_session
worker._run=namespace['NativeSourceWorker']._run
