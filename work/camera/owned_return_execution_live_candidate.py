"""Isolated transaction backend selection; preserve installed owner methods."""
import ctypes as C,types,inspect,os
from pathlib import Path
import owned_native_transaction_worker_install_candidate as tx
from owned_uncovered_window_candidate import OwnedD3DConsumer
loads=[]
class Loader:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ("owned-d3d-call-profile-candidate.dll","owned-d3d-present-batch-candidate.dll","owned-d3d-native-transaction-candidate.dll"):
   path=str(Path(path).with_name("owned-d3d-return-execution-candidate.dll"))
  if os.environ.get('NFSUG_HUD_PHASE_CYCLES')=='1' and Path(path).name=='owned-d3d-return-execution-candidate.dll':path=str(Path(path).with_name('owned-d3d-hud-cycles-return-execution.dll'))
  if os.environ.get('NFSUG_HUD_DISCARD_TEXTURE')=='1' and Path(path).name in ('owned-d3d-return-execution-candidate.dll','owned-d3d-hud-cycles-return-execution.dll'):path=str(Path(path).with_name('owned-d3d-hud-discard-return-execution.dll'))
  result=C.CDLL(path,*args,**kwargs)
  if Path(path).name in ("owned-d3d-return-execution-candidate.dll","owned-d3d-hud-cycles-return-execution.dll","owned-d3d-hud-discard-return-execution.dll"):loads.append(result._name)
  return result
original=tx.selected
replacement=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
source=inspect.getsource(tx.init).replace("owned-d3d-native-transaction-candidate.dll","owned-d3d-hud-discard-return-execution.dll" if os.environ.get("NFSUG_HUD_DISCARD_TEXTURE")=="1" else ("owned-d3d-hud-cycles-return-execution.dll" if os.environ.get("NFSUG_HUD_PHASE_CYCLES")=="1" else "owned-d3d-return-execution-candidate.dll"))
namespace=dict(tx.init.__globals__,replacement=replacement)
exec(compile(source,"isolated-alpha-sky-init","exec"),namespace)
OwnedD3DConsumer.__init__=namespace["init"]

# All getters run synchronously inside the renderer owner methods.
U=C.c_uint64
rows=[]
prepare_original=tx.Session.prepare
commit_original=tx.Session.commit_present
def measured(self):
 out=(U*12)()
 fn=self.consumer.d.nf_d3d_measured_stages
 fn.argtypes=[C.c_void_p,C.c_size_t]
 assert fn(out,C.sizeof(out))==0
 return list(out)
def prepare(self,owned,e,g,i):
 result=prepare_original(self,owned,e,g,i)
 result['native_stage_cycles_prepare']=dict(identity=[e,g,i],values=measured(self))
 return result
def commit(self,payload,e,g,i):
 result=commit_original(self,payload,e,g,i)
 result['native_stage_cycles_present']=dict(identity=[e,g,i],values=measured(self))
 if result['native_result']==1:
  assert len(rows)<8192
  rows.append(dict(identity=[e,g,i],values=result['native_stage_cycles_present']['values']))
 return result
tx.Session.prepare=prepare
tx.Session.commit_present=commit

def save():
 import json,time
 path=Path('work/camera/prototype-runs')/('native-stage-cycles-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(rows=rows,capacity=8192,scope='Successful owner-thread commits; last world batch only, not total ordered scene draw. Raw cycles are not elapsed time.'),indent=2))
 print('NATIVE_STAGE_CYCLES',path,flush=True)

# Sample Python-side execution before extra getter calls, on the same owner thread.
from owned_thread_cycles import read as cycle_read,held_kernel
class FileTime(C.Structure):
 _fields_=[('low',C.c_uint32),('high',C.c_uint32)]
get_times=held_kernel.GetThreadTimes
get_times.argtypes=[C.c_void_p,*([C.POINTER(FileTime)]*4)];get_times.restype=C.c_int
get_current=held_kernel.GetCurrentThread;get_current.restype=C.c_void_p
def cpu_read():
 a,b,k,u=(FileTime() for _ in range(4))
 assert get_times(get_current(),C.byref(a),C.byref(b),C.byref(k),C.byref(u))
 return (k.high<<32|k.low)+(u.high<<32|u.low)
function_source=inspect.getsource(tx.commit_present)
needle='end=time.perf_counter_ns()'
assert function_source.count(needle)==1
function_source=function_source.replace(needle,needle+";returned_cycles=cycle_read();returned_cpu=cpu_read()\n profile=(U*4)();getter=self.consumer.d.nf_d3d_return_execution;getter.argtypes=[P,C.c_size_t];assert getter(profile,C.sizeof(profile))==0\n return_execution=dict(identity=[e,g,i],native=list(profile),python_return_ns=end,python_cycles=returned_cycles,python_cpu_100ns=returned_cpu)")
function_source=function_source.replace('return dict(native_result=result,','return dict(return_execution=return_execution,native_result=result,')
ns=dict(tx.commit_present.__globals__,cycle_read=cycle_read,cpu_read=cpu_read)
exec(compile(function_source,'native-return-execution-worker','exec'),ns)
commit_original=ns['commit_present']
