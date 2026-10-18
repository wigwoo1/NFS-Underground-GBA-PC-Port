"""Select isolated bound HUD short-lock bundle; unchanged renderer source function."""
import types,ctypes as C
import owned_native_source_hud_cache_lease_session_candidate as hud
loads=[]
original=hud.NativeSourceSession.__init__
class Loader:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  path=str(path)
  if path.endswith('owned-gpu-source-packet-profile-candidate.dll'):
   path=path[:-len('owned-gpu-source-packet-profile-candidate.dll')]+'owned-gpu-source-packet-short-lock-candidate.dll'
  result=C.CDLL(path,*args,**kwargs)
  if path.endswith("owned-gpu-source-packet-short-lock-candidate.dll"):loads.append(result._name)
  return result
hud.NativeSourceSession.__init__=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
