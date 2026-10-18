import ctypes as C,types
from pathlib import Path
import owned_native_source_hud_cache_lease_session_candidate as session
import owned_hud_short_lock_renderer_install_candidate as selected
loads=[]
class Loader:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ('owned-gpu-source-packet-profile-candidate.dll','owned-gpu-source-packet-short-lock-candidate.dll'):path=str(Path(path).with_name('owned-gpu-source-profile-provenance-candidate.dll'))
  result=C.CDLL(path,*args,**kwargs)
  if Path(path).name=='owned-gpu-source-profile-provenance-candidate.dll':loads.append(result._name);selected.loads.append(result._name)
  return result
original=session.NativeSourceSession.__init__
session.NativeSourceSession.__init__=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
