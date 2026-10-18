import ast,ctypes as C,time
from pathlib import Path
source=Path('work/camera/live_owned_gpu_worker.py').read_text();tree=ast.parse(source);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef));poll=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='poll_gpu_timer');ns=dict(C=C,time=time);exec(compile(ast.Module(body=[poll],type_ignores=[]),'actual_worker_poll','exec'),ns)
class Read:
 status=38
 def __call__(self,p):C.cast(p,C.POINTER(C.c_uint64))[0]=123;return self.status
class GPU:nf_owned_gpu_timer_read=Read()
class Worker:pending_gpu_timer=-1;results=[dict(gpu_timer_async=False)]
w=Worker();g=GPU();ns['poll_gpu_timer'](w,g);assert w.pending_gpu_timer==-1 and 'gpu_elapsed_ns' not in w.results[0]
g.nf_owned_gpu_timer_read.status=0;ns['poll_gpu_timer'](w,g);assert w.pending_gpu_timer is None and 'gpu_elapsed_ns' not in w.results[0]
w.pending_gpu_timer=0;w.results=[dict(gpu_timer_async=True)];ns['poll_gpu_timer'](w,g);assert w.results[0]['gpu_elapsed_ns']==123 and w.pending_gpu_timer is None
w.pending_gpu_timer=0;w.results=[dict(gpu_timer_async=False)]
try:ns['poll_gpu_timer'](w,g)
except AssertionError:pass
else:raise AssertionError('Bad association accepted')
fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='_draw_intervals');branch=next(x for x in ast.walk(fn) if isinstance(x,ast.If) and isinstance(x.test,ast.UnaryOp) and isinstance(x.test.operand,ast.Call) and isinstance(x.test.operand.func,ast.Attribute) and x.test.operand.func.attr=='wait_until')
class Cancel:
 pending_gpu_timer=7
 def wait_until(self,*args):return False
for queried in (True,False):
 obj=Cancel();wrapper=ast.FunctionDef(name='cancel',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='async_query')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[branch],decorator_list=[]);mod=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]));n=dict(slot=dict(deadline_ns=1),wait_revision=0);exec(compile(mod,'actual_cancel_branch','exec'),n);assert n['cancel'](obj,queried) is False;assert obj.pending_gpu_timer==(-1 if queried else 7)
print('PASS: actual canceled-slot branch, pending-not-ready ownership, orphan discard, valid association and invalid-row rejection')
