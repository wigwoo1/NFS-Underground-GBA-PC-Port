"""Submit prepared native deadline transaction without Python present callback."""
import ctypes as C,time
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic=False,on_prepared=None):
 pending=False;begin=time.perf_counter_ns();timing={}
 try:
  timing['draw_begin_ns']=time.perf_counter_ns()
  prepared=self.worker.prepare(owned,epoch,generation,index,diagnostic).result(timeout=20)
  pending=True;timing['draw_end_ns']=time.perf_counter_ns()
  if on_prepared:on_prepared()
  timing['present_begin_ns']=time.perf_counter_ns()
  tx=self.worker.commit_present(C.cast(self.f,C.c_void_p),self.owner,epoch,generation,older,newer,index,alpha,deadline).result(timeout=20)
  timing['present_end_ns']=time.perf_counter_ns()
  if tx['native_callback_count']:pending=False
  if tx['native_result']==-2:raise RuntimeError('Native transaction argument or owner failure')
  if tx['native_callback_count'] and tx['native_batch_result']!=0:
   raise RuntimeError('Native transaction batch failure: '+str(tx['native_batch_result']))
  return dict(callback_timing=timing,transaction_begin_ns=begin,transaction_end_ns=time.perf_counter_ns(),native_result=tx['native_result'],commit=tx['commit'],wait=tx['wait'],stages=tx['stages'],prepared=prepared,presentation=tx['presentation'],native_transaction=tx)
 finally:
  if pending:self.worker.abort(epoch,generation,index).result(timeout=20)
NativeSourceCommitAdapter.run=run
