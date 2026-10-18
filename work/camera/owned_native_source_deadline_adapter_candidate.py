import time
class NativeSourceCommitAdapter:
 def __init__(self,worker,owner):self.worker=worker;self.owner=owner
 def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic=False,on_prepared=None):
  assert not diagnostic and on_prepared is None
  began=time.perf_counter_ns()
  result=self.worker.timed(owned,self.owner,epoch,generation,older,newer,index,alpha,deadline).result(timeout=20)
  result.update(transaction_begin_ns=began,transaction_end_ns=time.perf_counter_ns(),native_deadline_path=True)
  return result
