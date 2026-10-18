"""Isolated adapter DLL selection; preserve callbacks, deadlines and commit semantics."""
import ctypes as C,types
from pathlib import Path
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
original=NativeSourceCommitAdapter.__init__
class LocalCTypes:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name=='owned-draw-commit-candidate.dll':path=str(Path(path).with_name('owned-draw-commit-highres-candidate.dll'))
  return C.CDLL(path,*args,**kwargs)
ns=dict(original.__globals__,C=LocalCTypes())
replacement=types.FunctionType(original.__code__,ns,original.__name__,original.__defaults__,original.__closure__)
def init(self,worker,owner):
 replacement(self,worker,owner)
 assert Path(self.d._name).name=='owned-draw-commit-highres-candidate.dll'
NativeSourceCommitAdapter.__init__=init
