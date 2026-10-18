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
   path=str(Path(path).with_name("owned-d3d-async-sky-coverage-transaction-candidate.dll"))
  result=C.CDLL(path,*args,**kwargs)
  if Path(path).name=="owned-d3d-async-sky-coverage-transaction-candidate.dll":loads.append(result._name)
  return result
original=tx.selected
replacement=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
source=inspect.getsource(tx.init).replace("owned-d3d-native-transaction-candidate.dll","owned-d3d-async-sky-coverage-transaction-candidate.dll")
namespace=dict(tx.init.__globals__,replacement=replacement)
exec(compile(source,"isolated-alpha-sky-init","exec"),namespace)
OwnedD3DConsumer.__init__=namespace["init"]
