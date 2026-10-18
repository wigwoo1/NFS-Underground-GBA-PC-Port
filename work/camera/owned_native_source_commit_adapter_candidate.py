"""Use existing native handoff authority for D3D prepare/wait/present."""
import ctypes as C
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
class NativeSourceCommitAdapter:
 def __init__(self,worker,owner):
  self.worker=worker;self.owner=owner;self.d=C.CDLL(str((Path(__file__).parent/'owned-draw-commit-candidate.dll').resolve()));self.f=self.d.nf_owned_handoff_draw_wait_commit_sample;self.f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
 def run(self,owned,epoch,generation,older,newer,index,alpha,deadline,diagnostic=False,on_prepared=None):
  state=dict(pending=False,errors=[]);worker=self.worker
  @CB
  def draw(ctx):
   try:
    state['prepared']=worker.prepare(owned,epoch,generation,index,diagnostic).result(timeout=20);state['pending']=True
    if on_prepared:on_prepared()
    return 0
   except BaseException as error:state['errors'].append(error);return 9
  @CB
  def present(ctx):
   try:
    state['presentation']=worker.present(epoch,generation,index).result(timeout=20);state['pending']=False
    return int(state['presentation']['status']==0)
   except BaseException as error:state['errors'].append(error);return 0
  out=(U*8)(*[123]*8);wait=(U*4)();stages=(U*7)()
  try:result=self.f(self.owner,epoch,generation,older,newer,index,alpha,deadline,draw,None,present,None,out,wait,stages)
  finally:
   if state['pending']:worker.abort(epoch,generation,index).result(timeout=20)
  if state['errors']:raise state['errors'][0]
  return dict(native_result=result,commit=list(out),wait=list(wait),stages=list(stages),prepared=state.get('prepared'),presentation=state.get('presentation'))
