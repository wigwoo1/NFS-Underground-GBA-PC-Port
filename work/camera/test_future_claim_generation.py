import ast,ctypes as C,threading
from pathlib import Path
from types import SimpleNamespace
s=ast.parse(Path('work/camera/live_owned_gpu_worker.py').read_text());method=next(n for n in ast.walk(s) if isinstance(n,ast.FunctionDef) and n.name=='_draw_intervals');branch=next(n for n in ast.walk(method) if isinstance(n,ast.If) and ast.unparse(n.test)=='self.preparation_service is not None')
body=branch.body;stop=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='future' for t in n.targets));body=body[:stop+1]+[ast.Return(ast.Name('future',ast.Load()))]
fn=ast.FunctionDef(name='claim',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=k) for k in ('self','previous','scene','epoch','generation','Callback')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[]);ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'actual-future-claim','exec'),ns)
d=C.CDLL(str(Path('work/camera/owned-frame-handoff.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P);d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P]
q=d.nf_owned_handoff_create(9);a=SimpleNamespace(identity=(9,1));b=SimpleNamespace(identity=(9,2));key=(a.identity,b.identity);value=object();w=SimpleNamespace(d=d,owner=q,scene_snapshot_lock=threading.Lock(),preparation_futures={key:value})
try:
 assert d.nf_owned_handoff_pause(q,1);assert d.nf_owned_handoff_pause(q,0)
 assert ns['claim'](w,(None,None,None,a),b,9,1,Callback) is False;assert w.preparation_futures[key] is value
 assert ns['claim'](w,(None,None,None,a),b,9,3,Callback) is value;assert key not in w.preparation_futures
 print('PASS: retired token cannot steal rebuilt future; valid generation claims exactly once')
finally:d.nf_owned_handoff_destroy(q)
