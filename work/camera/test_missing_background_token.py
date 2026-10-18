"""Missing preparation is tolerated only for a natively retired token."""
import ast,ctypes as C
from pathlib import Path
from types import SimpleNamespace
source=ast.parse(Path(__file__).with_name('live_owned_gpu_worker.py').read_text())
method=next(n for n in ast.walk(source) if isinstance(n,ast.FunctionDef) and n.name=='_draw_intervals')
branch=next(n for n in ast.walk(method) if isinstance(n,ast.If) and ast.unparse(n.test)=='future is None')
fn=ast.FunctionDef(name='check',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('self','epoch','generation','Callback','future')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[branch],decorator_list=[])
module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns={};exec(compile(module,'actual-missing-future-branch','exec'),ns)
from concurrent.futures import CancelledError
cancel_branch=next(n for n in ast.walk(method) if isinstance(n,ast.Try) and any(isinstance(h.type,ast.Name) and h.type.id=='CancelledError' for h in n.handlers))
fn2=ast.FunctionDef(name='cancel_check',args=fn.args,body=[cancel_branch],decorator_list=[])
ns['CancelledError']=CancelledError
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn2],type_ignores=[])),'actual-cancelled-future-branch','exec'),ns)
class CancelService:
 def take(self,future):raise CancelledError()
d=C.CDLL(str(Path(__file__).with_name('owned-frame-handoff.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p
d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint]
d.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
Callback=C.CFUNCTYPE(C.c_int,C.c_void_p)
d.nf_owned_handoff_commit_token.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,Callback,C.c_void_p]
owner=d.nf_owned_handoff_create(9);assert owner
w=SimpleNamespace(d=d,owner=owner)
w.preparation_service=CancelService()
try:
 try:ns['cancel_check'](w,9,1,Callback,None)
 except CancelledError:pass
 else:raise AssertionError('Valid token cancellation was silently accepted')
 try:ns['check'](w,9,1,Callback,None)
 except ValueError as e:assert str(e)=='Missing owned background interval'
 else:raise AssertionError('Valid missing interval was silently accepted')
 assert d.nf_owned_handoff_pause(owner,1)
 assert ns['check'](w,9,1,Callback,None) is False
 assert ns['cancel_check'](w,9,1,Callback,None) is False
 assert d.nf_owned_handoff_pause(owner,0)
 assert ns['check'](w,9,1,Callback,None) is False
 assert ns['cancel_check'](w,9,1,Callback,None) is False
 assert ns['check'](w,9,3,Callback,object()) is None
finally:d.nf_owned_handoff_destroy(owner)
print('PASS: valid missing interval rejects; paused and resumed retired tokens cancel; existing future bypasses probe')
