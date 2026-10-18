import ctypes as C,json
from pathlib import Path
from owned_ordered_render_tail_binding_candidate import Tail,bridge,address
p=C.CDLL(str(Path('work/camera/ordered-render-tail-profile-candidate.dll').resolve()));p.nf_ordered_render_tail_profile.argtypes=[C.POINTER(Tail),C.c_size_t,C.POINTER(C.c_uint),C.POINTER(C.c_uint64)]
S=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p);W=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_size_t);H=C.CFUNCTYPE(C.c_int,*([C.c_void_p]*4))
trace=[];failure=[0]
def call(stage):
 trace.append(stage);return 17 if failure[0]==stage else 0
sky=S(lambda *x:call(1));world=W(lambda *x:call(2));hud=H(lambda *x:call(3))
j=Tail(address(sky),address(world),address(hud),1,1,1,1,1,1,1,0,0,1,4,1,0,1,0,0)
checks=0
for fail in range(4):
 failure[0]=fail;results=[]
 for profiled in [False,True]:
  trace.clear();failed=C.c_uint(123);ticks=(C.c_uint64*7)()
  code=p.nf_ordered_render_tail_profile(C.byref(j),C.sizeof(j),C.byref(failed),ticks) if profiled else bridge.nf_ordered_render_tail(C.byref(j),C.sizeof(j),C.byref(failed))
  results.append((code,failed.value,tuple(trace)))
  if profiled:
   used=6 if fail==0 else fail*2;assert ticks[0]>0 and all(ticks[i]<=ticks[i+1] for i in range(1,used));assert all(t==0 for t in ticks[used+1:])
 assert results[0]==results[1];checks+=1
for field,value in [('sky',0),('world',0),('hud',0),('vb',1),('ob',0),('ib',1),('sb',1),('nv',65537),('nd',4097)]:
 old=getattr(j,field);setattr(j,field,value);trace.clear();f=C.c_uint(123);ticks=(C.c_uint64*7)();assert p.nf_ordered_render_tail_profile(C.byref(j),C.sizeof(j),C.byref(f),ticks)==37 and not trace;setattr(j,field,old);checks+=1
out=dict(result='PASS_ORDERED_TAIL_PROFILE_ORDER_ERRORS_ABI',checks=checks,scope='Exact original call order/error stage and invalid ABI guards with fake native callbacks; actual4K and live tests separate.')
Path('work/camera/prototype-runs/ordered-tail-profile-guards-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
