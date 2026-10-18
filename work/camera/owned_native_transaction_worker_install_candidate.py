"""Owner-renderer commit job; real caller authority and sample identities."""
import ctypes as C,time,types
from pathlib import Path
import owned_present_batch_backend_install_candidate as batch
import owned_renderer_dispatch_trace_install_candidate as dispatch
import owned_native_source_segmented_release_worker_candidate as module
from owned_uncovered_window_candidate import OwnedD3DConsumer
U=C.c_uint64;P=C.c_void_p;Output=U*48
selected=batch.replacement
class LocalCTypes:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ('owned-d3d-call-profile-candidate.dll','owned-d3d-present-batch-candidate.dll'):
   path=str(Path(path).with_name('owned-d3d-native-transaction-candidate.dll'))
  return C.CDLL(path,*args,**kwargs)
replacement=types.FunctionType(selected.__code__,dict(selected.__globals__,C=LocalCTypes()),selected.__name__,selected.__defaults__,selected.__closure__)
def init(self):
 replacement(self)
 assert Path(self.d._name).name=='owned-d3d-native-transaction-candidate.dll'
 self.d.nf_d3d_hud_phase_ticks.argtypes=[P,C.c_size_t]
 self.d.nf_d3d_native_transaction.argtypes=[P,P,P,U,U,U,U,U,C.c_double,U,P,C.c_size_t]
OwnedD3DConsumer.__init__=init
worker=module.NativeSourceWorker
Session=worker._run.__globals__['NativeSourceSession']
Error=worker._run.__globals__['NativeFrameIdentityError']
def commit_present(self,payload,e,g,i):
 if self.closed or self.pending!=(e,g,i):raise Error('Native transaction pending identity mismatch')
 authority,owner,older,newer,alpha,deadline=payload
 values=Output();begin=time.perf_counter_ns()
 result=self.consumer.d.nf_d3d_native_transaction(authority,owner,self.consumer.window,e,g,older,newer,i,alpha,deadline,values,C.sizeof(values))
 end=time.perf_counter_ns()
 if values[46]:self.pending=None
 v=values[19:46]
 presentation=None
 if values[46] and values[47]==0:
  presentation=dict(status=v[0],window=list(v[1:8]),dxgi_display_stats=list(v[8:17]),present_stage_ns=dict(zip(('begin','pumped','presented','queried'),v[17:21])),native_present_ticks=list(v[21:27]))
 return dict(native_result=result,commit=list(values[:8]),wait=list(values[8:12]),stages=list(values[12:19]),presentation=presentation,native_callback_count=values[46],native_batch_result=C.c_int64(values[47]).value,transaction_begin_ns=begin,transaction_end_ns=end)
Session.commit_present=commit_present
# Retain the selected class and all its other installed methods.
import owned_hud_prefetch_d3d_profile_install_candidate as prefetch
source=prefetch.source
needle="elif kind=='present':result=session.present(e,g,i)"
assert source.count(needle)==1
source=source.replace(needle,needle+"\n     elif kind=='commit_present':result=session.commit_present(owned,e,g,i)")
namespace=dict(worker._run.__globals__)
exec(compile(source,'native-owner-transaction-worker','exec'),namespace)
namespace['NativeSourceSession']=Session
worker._run=namespace['NativeSourceWorker']._run
def submit_commit(self,authority,owner,e,g,older,newer,i,alpha,deadline):
 return self._submit('commit_present',(authority,owner,older,newer,alpha,deadline),e,g,i)
worker.commit_present=submit_commit
