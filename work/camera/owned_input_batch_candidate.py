"""Isolated native input poll/snapshot batching; original input authority retained."""
import ctypes as C,threading,time,json,atexit,os
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as module
class Result(C.Structure):
 _fields_=[('state',C.c_uint32*4),('elapsed',C.c_uint64),('stages',C.c_uint64*4),('message',C.c_uint64*6)]
assert C.sizeof(Result)==104
library=C.CDLL(str(Path(__file__).with_name('input-poll-snapshot-batch.dll').resolve()))
fn=library.nf_input_poll_snapshot_batch;fn.argtypes=[C.c_void_p]*5+[C.c_uint,C.c_void_p,C.c_size_t];fn.restype=C.c_int
records=[]
def poll_input(self,session):
 assert threading.get_ident()==self.thread.ident
 s=session.source
 if not hasattr(self,'input_batch_owner'):
  self.input_batch_owner=s;self.input_batch_result=Result()
  names=('nf_owned_input_poll','nf_owned_input_poll_timed','nf_owned_input_stages','nf_owned_input_message_profile','nf_owned_input_snapshot')
  flags=3 if self.input_poll_trace and hasattr(s,names[3]) else 1 if self.input_poll_trace else 0
  needed={0,4} if flags==0 else {1,2,4}|({3} if flags==3 else set())
  self.input_batch_arguments=tuple(C.cast(getattr(s,name),C.c_void_p) if i in needed else None for i,name in enumerate(names))+(flags,)
  self.input_batch_stats=dict(initializations=1,polls=0,traced=self.input_poll_trace,flags=flags,closed=False,released=False);records.append(self.input_batch_stats)
 elif self.input_batch_owner is not s:raise RuntimeError('Input batch source owner changed')
 out=self.input_batch_result;status=fn(*self.input_batch_arguments,C.byref(out),C.sizeof(out))
 if status:raise RuntimeError('Native input batch failed: '+str(status))
 if self.input_poll_trace:
  self.last_input_poll_stages=dict(zip(('total_ns','message_pump_ns','keyboard_ns','controller_ns','snapshot_ns'),(out.elapsed,*out.stages)))
  message=None
  if self.input_batch_arguments[-1]==3:
   message=dict(zip(('message','begin_ns','end_ns','wparam','lparam','processed'),out.message));self.last_input_message_profile=message
  self.input_poll_ledger.observe(self.last_input_poll_stages,message)
 with self.input_lock:
  self.input_state=tuple(out.state);self.input_polls+=1;self.input_poll_thread=threading.get_ident()
 self.input_batch_stats['polls']+=1

def release(self):
 if self.thread.is_alive():raise RuntimeError('Cannot release live input batch owner')
 for name in ('input_batch_owner','input_batch_result','input_batch_arguments'):
  if hasattr(self,name):delattr(self,name)
 if hasattr(self,'input_batch_stats'):self.input_batch_stats.update(closed=True,released=True)

def install():
 cls=module.NativeSourceWorker
 if getattr(cls,'input_batch_candidate',False):return
 if getattr(cls,'input_scratch_candidate',False):raise RuntimeError('Conflicting input candidate')
 old=cls.close
 def close(self):
  try:return old(self)
  finally:
   if not self.thread.is_alive():release(self)
 cls._poll_input=poll_input;cls.close=close;cls.input_batch_candidate=True

def save():
 if not records:return
 p=Path('work/camera/prototype-runs')/('input-batch-execution-'+str(time.time_ns())+'.json');p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(dict(records=records,scope='Native input batch executions and joined owner release; no cadence/physical Xbox proof.'),indent=2));print('INPUT_BATCH_EXECUTION',p)
atexit.register(save)
selected=os.environ.get('NFSUG_INPUT_BATCH_SELECT','1')=='1'
if selected:install()
print('INPUT_BATCH_SELECTION',selected)
