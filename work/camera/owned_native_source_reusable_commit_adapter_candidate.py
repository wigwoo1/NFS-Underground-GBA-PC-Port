"""Use existing native handoff authority for D3D prepare/wait/present."""
import ctypes as C,time,threading
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class NativeSourceCommitAdapter:
 def __init__(self,worker,owner):
  self.worker=worker;self.owner=owner;self.d=C.CDLL(str((Path(__file__).parent/'owned-draw-commit-candidate.dll').resolve()));self.f=self.d.nf_owned_handoff_draw_wait_commit_sample;self.f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
  self.thread=threading.get_ident();self.busy=False;self.active_state=None;self.active_args=None
  self.output=(U*8)();self.wait_output=(U*4)();self.stage_output=(U*7)();self.draw_callback=CB(self._draw);self.present_callback=CB(self._present)
 def _draw(self,ctx):
  state=self.active_state;worker=self.worker
  owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic,on_prepared=self.active_args
  try:
   state['draw_begin_ns']=time.perf_counter_ns()
   state['prepared']=worker.prepare(owned,epoch,generation,index,diagnostic).result(timeout=20);state['pending']=True;state['draw_end_ns']=time.perf_counter_ns()
   if on_prepared:on_prepared()
   return 0
  except BaseException as error:state['errors'].append(error);return 9
 def _present(self,ctx):
  state=self.active_state;worker=self.worker
  owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic,on_prepared=self.active_args
  try:
   state['present_begin_ns']=time.perf_counter_ns()
   state['presentation']=worker.present(epoch,generation,index).result(timeout=20);state['pending']=False;state['present_end_ns']=time.perf_counter_ns()
   return int(state['presentation']['status']==0)
  except BaseException as error:state['errors'].append(error);return 0
 def run(self,*args,**kwargs):
  if threading.get_ident()!=self.thread:raise RuntimeError('Adapter owner thread mismatch')
  if self.busy:raise RuntimeError('Adapter reentrant transaction')
  self.busy=True
  try:return self._run(*args,**kwargs)
  finally:self.active_state=None;self.active_args=None;self.busy=False
 def _run(self,owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic=False,on_prepared=None):
  state=dict(pending=False,errors=[]);worker=self.worker
  self.active_state=state;self.active_args=(owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic,on_prepared)
  draw,present=self.draw_callback,self.present_callback
  out,wait,stages=self.output,self.wait_output,self.stage_output
  for i in range(8):out[i]=123
  for i in range(4):wait[i]=0
  for i in range(7):stages[i]=0
  call_begin=time.perf_counter_ns()
  try:result=self.f(self.owner,epoch,generation,older,newer,index,alpha,deadline,draw,None,present,None,out,wait,stages)
  finally:
   if state['pending']:worker.abort(epoch,generation,index).result(timeout=20)
  if state['errors']:raise state['errors'][0]
  return dict(callback_timing={k:v for k,v in state.items() if k.endswith('_ns')},transaction_begin_ns=call_begin,transaction_end_ns=time.perf_counter_ns(),native_result=result,commit=list(out),wait=list(wait),stages=list(stages),prepared=state.get('prepared'),presentation=state.get('presentation'))
