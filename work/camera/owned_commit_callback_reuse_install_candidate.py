"""Private adapter callback reuse; per-call state/owned draw never escapes sync call."""
import ctypes as C,inspect,textwrap,threading,weakref
import owned_native_source_timed_commit_adapter_candidate as module
stats=dict(adapters=0,callback_instances=0,calls=0,draw_callbacks=0,present_callbacks=0,active=0)
Base=module.NativeSourceCommitAdapter
class ReusedAdapter(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self._current=None;self._thread=threading.get_ident();self._install_callbacks()
 def _install_callbacks(self):
  stats["adapters"]+=1;stats["callback_instances"]+=2
  ref=weakref.ref(self)
  @module.CB
  def draw(ctx):
   stats["draw_callbacks"]+=1
   obj=ref()
   if obj is None or obj._current is None or threading.get_ident()!=obj._thread:return 9
   state,owned,epoch,generation,index,diagnostic,on_prepared=obj._current
   try:
    state['draw_begin_ns']=module.time.perf_counter_ns();state['prepared']=obj.worker.prepare(owned,epoch,generation,index,diagnostic).result(timeout=20);state['pending']=True;state['draw_end_ns']=module.time.perf_counter_ns()
    if on_prepared:on_prepared()
    return 0
   except BaseException as error:state['errors'].append(error);return 9
  @module.CB
  def present(ctx):
   stats["present_callbacks"]+=1
   obj=ref()
   if obj is None or obj._current is None or threading.get_ident()!=obj._thread:return 0
   state,owned,epoch,generation,index,diagnostic,on_prepared=obj._current
   try:
    state['present_begin_ns']=module.time.perf_counter_ns();state['presentation']=obj.worker.present(epoch,generation,index).result(timeout=20);state['pending']=False;state['present_end_ns']=module.time.perf_counter_ns();return int(state['presentation']['status']==0)
   except BaseException as error:state['errors'].append(error);return 0
  self._draw_callback=draw;self._present_callback=present
 def run(self,*args,**kwargs):
  if threading.get_ident()!=self._thread or self._current is not None:raise RuntimeError('Commit adapter thread/re-entry mismatch')
  stats["calls"]+=1;stats["active"]+=1
  try:return self._run_reused(*args,**kwargs)
  finally:self._current=None;stats["active"]-=1
source=textwrap.dedent(inspect.getsource(Base.run));start=source.index(' @CB');end=source.index(' out=(U*8)',start)
source=source[:start]+" self._current=(state,owned,epoch,generation,index,diagnostic,on_prepared)\n draw=self._draw_callback;present=self._present_callback\n"+source[end:]
source=source.replace('def run(', 'def _run_reused(',1)
ns=dict(Base.run.__globals__);exec(compile(source,'reused-commit-callbacks','exec'),ns);ReusedAdapter._run_reused=ns['_run_reused']
module.NativeSourceCommitAdapter=ReusedAdapter
