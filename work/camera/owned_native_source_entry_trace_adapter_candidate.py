"""Use existing native handoff authority for D3D prepare/wait/present."""
import ctypes as C,time
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class NativeSourceCommitAdapter:
 def __init__(self,worker,owner):
  self.worker=worker;self.owner=owner;self.d=C.CDLL(str((Path(__file__).parent/'owned-draw-entry-trace-candidate.dll').resolve()));self.f=self.d.nf_owned_handoff_draw_wait_commit_sample;self.f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
 def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic=False,on_prepared=None):
  state=dict(pending=False,errors=[]);worker=self.worker
  @CB
  def draw(ctx):
   try:
    state['draw_begin_ns']=time.perf_counter_ns()
    state['prepared']=worker.prepare(owned,epoch,generation,index,diagnostic).result(timeout=20);state['pending']=True;state['draw_end_ns']=time.perf_counter_ns()
    if on_prepared:on_prepared()
    return 0
   except BaseException as error:state['errors'].append(error);return 9
  @CB
  def present(ctx):
   try:
    state['present_begin_ns']=time.perf_counter_ns()
    state['presentation']=worker.present(epoch,generation,index).result(timeout=20);state['pending']=False;state['present_end_ns']=time.perf_counter_ns()
    return int(state['presentation']['status']==0)
   except BaseException as error:state['errors'].append(error);return 0
  out=(U*8)(*[123]*8);wait=(U*4)();stages=(U*7)()
  call_begin=time.perf_counter_ns()
  try:
   result=self.f(self.owner,epoch,generation,older,newer,index,alpha,deadline,draw,None,present,None,out,wait,stages)
   native_trace=(U*9)();self.d.nf_owned_entry_trace(native_trace)
  finally:
   if state['pending']:worker.abort(epoch,generation,index).result(timeout=20)
  if state['errors']:raise state['errors'][0]
  return dict(native_entry_trace=list(native_trace),callback_timing={k:v for k,v in state.items() if k.endswith('_ns')},transaction_begin_ns=call_begin,transaction_end_ns=time.perf_counter_ns(),native_result=result,commit=list(out),wait=list(wait),stages=list(stages),prepared=state.get('prepared'),presentation=state.get('presentation'))

