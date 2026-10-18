"""Isolated transaction backend selection; preserve installed owner methods."""
import ctypes as C,types,inspect,os
from pathlib import Path
import owned_native_transaction_worker_install_candidate as tx
from owned_uncovered_window_candidate import OwnedD3DConsumer
loads=[]
floor_enabled=os.environ.get('NFSUG_PRESENT_FLOOR')=='1'
if floor_enabled:assert os.environ.get('NFSUG_CLOCK_PRESENT')=='1' and os.environ.get('NFSUG_HUD_PHASE_CYCLES')!='1','Floor pacing requires isolated Present0 selection without HUD cycle backend'
floor_library='owned-d3d-start-floor-present-transaction-candidate.dll' if os.environ.get('NFSUG_PRESENT_FLOOR_START')=='1' else 'owned-d3d-floor-present-transaction-candidate.dll'
if os.environ.get('NFSUG_PRESENT_FLOOR_START')=='1':assert floor_enabled
class Loader:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ("owned-d3d-call-profile-candidate.dll","owned-d3d-present-batch-candidate.dll","owned-d3d-native-transaction-candidate.dll"):
   path=str(Path(path).with_name("owned-d3d-world-stream-linear-transaction-candidate.dll"))
  if os.environ.get('NFSUG_HUD_PHASE_CYCLES')=='1' and Path(path).name=='owned-d3d-world-stream-linear-transaction-candidate.dll':path=str(Path(path).with_name('owned-d3d-hud-cycles-linear-transaction-candidate.dll'))
  if os.environ.get('NFSUG_CLOCK_PRESENT')=='1' and Path(path).name=='owned-d3d-world-stream-linear-transaction-candidate.dll':path=str(Path(path).with_name('owned-d3d-clock-present-transaction-candidate.dll'))
  if floor_enabled and Path(path).name=='owned-d3d-clock-present-transaction-candidate.dll':path=str(Path(path).with_name(floor_library))
  result=C.CDLL(path,*args,**kwargs)
  if Path(path).name in ("owned-d3d-world-stream-linear-transaction-candidate.dll","owned-d3d-hud-cycles-linear-transaction-candidate.dll","owned-d3d-clock-present-transaction-candidate.dll","owned-d3d-floor-present-transaction-candidate.dll","owned-d3d-start-floor-present-transaction-candidate.dll"):loads.append(result._name)
  return result
original=tx.selected
replacement=types.FunctionType(original.__code__,dict(original.__globals__,C=Loader()),original.__name__,original.__defaults__,original.__closure__)
expected_library="owned-d3d-clock-present-transaction-candidate.dll" if os.environ.get("NFSUG_CLOCK_PRESENT")=="1" else "owned-d3d-world-stream-linear-transaction-candidate.dll"
if floor_enabled:expected_library=floor_library
source=inspect.getsource(tx.init).replace("owned-d3d-native-transaction-candidate.dll",expected_library)
namespace=dict(tx.init.__globals__,replacement=replacement)
exec(compile(source,"isolated-alpha-sky-init","exec"),namespace)
OwnedD3DConsumer.__init__=namespace["init"]


