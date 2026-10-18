"""Replace only the selected backend load in the existing consumer initializer."""
import ctypes as C,types
from pathlib import Path
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.__init__
class LocalCTypes:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name=='owned-d3d-call-profile-candidate.dll':path=str(Path(path).with_name('owned-d3d-present-batch-candidate.dll'))
  return C.CDLL(path,*args,**kwargs)
ns=dict(original.__globals__,C=LocalCTypes())
replacement=types.FunctionType(original.__code__,ns,original.__name__,original.__defaults__,original.__closure__)
def init(self):
 replacement(self)
 assert Path(self.d._name).name=='owned-d3d-present-batch-candidate.dll'
 self.d.nf_d3d_hud_phase_ticks.argtypes=[C.c_void_p,C.c_size_t]
OwnedD3DConsumer.__init__=init

def present(self):
 values=(C.c_uint64*27)();self.d.nf_d3d_present_batch.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 assert self.d.nf_d3d_present_batch(self.window,values,C.sizeof(values))==0
 return dict(status=values[0],window=list(values[1:8]),dxgi_display_stats=list(values[8:17]),present_stage_ns=dict(zip(('begin','pumped','presented','queried'),values[17:21])),native_present_ticks=list(values[21:27]))
OwnedD3DConsumer.present=present
