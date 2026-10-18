"""Isolated transaction backend selection; preserve installed owner methods."""
import ctypes as C,types,inspect
from pathlib import Path
import owned_native_transaction_worker_install_candidate as tx
from owned_uncovered_window_candidate import OwnedD3DConsumer
loads=[]
class Loader:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ("owned-d3d-call-profile-candidate.dll","owned-d3d-present-batch-candidate.dll","owned-d3d-native-transaction-candidate.dll"):
   path=str(Path(path).with_name("owned-d3d-stage-cycles-transaction-candidate.dll"))
  result=C.CDLL(path,*args,**kwargs)
  if Path(path).name=="owned-d3d-stage-cycles-transaction-candidate.dll":loads.append(result._name)
  return result
original=tx.selected
replacement=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
source=inspect.getsource(tx.init).replace("owned-d3d-native-transaction-candidate.dll","owned-d3d-stage-cycles-transaction-candidate.dll")
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
