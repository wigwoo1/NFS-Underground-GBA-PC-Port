import ctypes as C,json
from concurrent.futures import Future
from pathlib import Path
import owned_commit_callback_reuse_install_candidate as reuse
P=C.c_void_p;U=C.c_uint64
class Worker:
 def __init__(self):self.calls=[];self.failure=None
 def call(self,name):
  self.calls.append(name);f=Future()
  if self.failure==name:f.set_exception(ValueError(name))
  else:f.set_result({'status':0})
  return f
 def prepare(self,*a):return self.call('prepare')
 def present(self,*a):return self.call('present')
 def abort(self,*a):return self.call('abort')
d=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()));d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P;d.nf_owned_handoff_destroy.argtypes=[P];d.nf_owned_handoff_pause.argtypes=[P,C.c_uint]
results=[]
for cls in (reuse.Base,reuse.ReusedAdapter):
 q=d.nf_owned_handoff_create(7);assert q;w=Worker();a=cls(w,q);rows=[]
 try:
  for label,index,alpha,failure in [('success',20,.5,None),('draw_failure',21,.5,'prepare'),('present_failure',22,.5,'present'),('invalid_alpha',23,float('nan'),None)]:
   d.nf_owned_handoff_destroy(q);q=d.nf_owned_handoff_create(7);assert q;a.owner=q
   w.calls=[];w.failure=failure
   try:r=a.run(object(),7,1,10,14,index,alpha,0);result=r['native_result'];commit=r['commit']
   except ValueError as e:result=str(e);commit=None
   rows.append(dict(case=label,result=result,calls=list(w.calls),commit=commit))
   if cls is reuse.ReusedAdapter:assert a._current is None
  w.calls=[];w.failure=None
  r=a.run(object(),7,1,10,14,24,.5,0,on_prepared=lambda: d.nf_owned_handoff_pause(q,1))
  rows.append(dict(case='cancel_during_draw',result=r['native_result'],calls=list(w.calls),commit=r['commit']))
  w.calls=[];r=a.run(object(),7,1,10,14,25,.5,0);rows.append(dict(case='retired_token',result=r['native_result'],calls=list(w.calls),commit=r['commit']))
 finally:d.nf_owned_handoff_destroy(q)
 results.append(rows)
for rows in results:
 rows[0]['commit'][6]=0 # Independent native commit timestamps are intentionally different.
assert results[0]==results[1],results
assert [r['result'] for r in results[0]]==[1,'prepare','present',-1,0,0]
assert results[0][2]['calls']==['prepare','present','abort'] and results[0][4]['calls']==['prepare','abort'] and results[0][5]['calls']==[]
assert reuse.stats['active']==0
Path('work/camera/prototype-runs/reused-callback-native-failures-20261009.json').write_text(json.dumps(dict(result='PASS',cases=results[1],scope='Actual native handoff authority, Future-backed worker stand-ins; verifies callback error/abort/rejection equivalence, not actual GPU injected failure or scanout.'),indent=2));print('PASS_NATIVE_FAILURE_EQUIVALENCE')
