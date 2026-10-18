import sys,ctypes as C,gc,json,collections
from pathlib import Path
from concurrent.futures import Future
sys.path.insert(0,str(Path(__file__).parent))
import owned_present_batch_backend_install_candidate
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
baseline=NativeSourceCommitAdapter.run
class Worker:
 def __init__(self,fail=None):self.fail=fail;self.calls=[]
 def future(self,value,error=None):
  f=Future();f.set_exception(error) if error else f.set_result(value);return f
 def prepare(self,owned,e,g,i,diagnostic):
  self.calls.append(('prepare',owned,e,g,i,diagnostic));return self.future({'publication':[e,g,i]},ValueError('prepare failure') if self.fail=='prepare' else None)
 def present(self,e,g,i):
  self.calls.append(('present',e,g,i));return self.future({'status':0},ValueError('present failure') if self.fail=='present' else None)
 def abort(self,e,g,i):self.calls.append(('abort',e,g,i));return self.future(None)
policy=(gc.isenabled(),gc.get_threshold());results=[]
for name in ('original','fixed'):
 if name=='fixed':import owned_parent_fixed_abi_types_install_candidate as fixed
 method=baseline if name=='original' else NativeSourceCommitAdapter.run
 w=Worker();a=NativeSourceCommitAdapter(w,None);d=a.d;d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p;d.nf_owned_handoff_destroy.argtypes=[C.c_void_p];a.owner=d.nf_owned_handoff_create(1)
 try:
  gc.collect() # Offline boundary: clear prior variant graphs before measuring.
  normal_before=len(gc.get_objects())
  for i in range(100):
   r=method(a,'private source',1,1,1,2,i,.5,0);assert r['native_result']==1 and r['commit'][:5]==[1,1,1,2,i] and r['prepared']=={'publication':[1,1,i]} and r['presentation']=={'status':0}
  normal_after=len(gc.get_objects());debug=gc.get_debug();old=len(gc.garbage)
  try:
   gc.set_debug(gc.DEBUG_SAVEALL);collected=gc.collect();objects=gc.garbage[old:];types=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in objects);del objects;del gc.garbage[old:]
  finally:gc.set_debug(debug)
  results.append(dict(variant=name,before=normal_before,after=normal_after,collected=collected,types=dict(types)))
 finally:d.nf_owned_handoff_destroy(a.owner)
print(results)
assert results[0]['types'].get('_ctypes.PyCArrayType',0)>0 and results[1]['types'].get('_ctypes.PyCArrayType',0)==0
for fail in ('prepare','present'):
 w=Worker(fail);a=NativeSourceCommitAdapter(w,None);d.nf_owned_handoff_create.argtypes=[C.c_uint64];a.owner=d.nf_owned_handoff_create(1)
 try:
  try:a.run(None,1,1,1,2,0,.5,0)
  except ValueError as error:assert str(error)==fail+' failure'
  else:raise AssertionError(fail)
  assert sum(c[0]=='abort' for c in w.calls)==(fail=='present')
 finally:d.nf_owned_handoff_destroy(a.owner)
for type_ in fixed.TYPES.values():
 a,b=type_(),type_();assert C.addressof(a)!=C.addressof(b);a[0]=123;assert b[0]==0
assert policy==(gc.isenabled(),gc.get_threshold())
out=dict(result='PASS_PARENT_FIXED_ABI_PRIVATE_BUFFERS_ERRORS_AND_HEAP',results=results,private_types=len(fixed.TYPES),scope='Actual native handoff200successful samples/fresh source outputs; prepare/present exceptions and pending abort semantics, private typed buffers. NormalGC duringiterations; offline SAVEALL finalcensus restored. NotliveGCgain or fullscene60proof.')
Path('work/camera/prototype-runs/parent-fixed-abi-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)
