"""Fixture-only transaction presentation: separate authority, no live integration."""
import ctypes as C,types,time
from pathlib import Path
import owned_present_batch_backend_install_candidate as batch
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.__init__
class LocalCTypes:
 def __getattr__(self,name):return getattr(C,name)
 def CDLL(self,path,*args,**kwargs):
  if Path(path).name in ('owned-d3d-present-batch-candidate.dll','owned-d3d-call-profile-candidate.dll'):
   path=str(Path(path).with_name('owned-d3d-native-transaction-candidate.dll'))
  return C.CDLL(path,*args,**kwargs)
# The batch initializer is a wrapper; clone its nested selected-backend loader.
selected=batch.replacement
replacement=types.FunctionType(selected.__code__,dict(selected.__globals__,C=LocalCTypes()),selected.__name__,selected.__defaults__,selected.__closure__)
U=C.c_uint64;P=C.c_void_p;Output=U*48
def init(self):
 replacement(self)
 assert Path(self.d._name).name=='owned-d3d-native-transaction-candidate.dll'
 self.d.nf_d3d_hud_phase_ticks.argtypes=[P,C.c_size_t]
 self.authority=C.CDLL(str((Path(__file__).parent/'owned-draw-commit-highres-candidate.dll').resolve()))
 self.authority.nf_owned_handoff_create.argtypes=[U];self.authority.nf_owned_handoff_create.restype=P
 self.authority.nf_owned_handoff_destroy.argtypes=[P]
 self.fixture_owner=self.authority.nf_owned_handoff_create(2);assert self.fixture_owner
 self.fixture_index=0
 self.d.nf_d3d_native_transaction.argtypes=[P,P,P,U,U,U,U,U,C.c_double,U,P,C.c_size_t]
def present(self):
 values=Output();deadline=time.perf_counter_ns()+2_000_000
 result=self.d.nf_d3d_native_transaction(C.cast(self.authority.nf_owned_handoff_draw_wait_commit_sample,P),self.fixture_owner,self.window,2,1,10,11,self.fixture_index,.5,deadline,values,C.sizeof(values))
 assert result==1 and values[46]==1 and values[47]==0
 assert list(values[:5])==[2,1,10,11,self.fixture_index]
 assert values[9]==deadline and values[10]>=deadline and values[6]>=deadline
 assert values[7]==self.fixture_index+1
 assert list(values[12:19])==sorted(values[12:19])
 self.fixture_index+=1
 v=values[19:46]
 return dict(status=v[0],window=list(v[1:8]),dxgi_display_stats=list(v[8:17]),present_stage_ns=dict(zip(('begin','pumped','presented','queried'),v[17:21])),native_present_ticks=list(v[21:27]))
original_close=OwnedD3DConsumer.close
def close(self):
 try:return original_close(self)
 finally:
  if getattr(self,'fixture_owner',None):
   self.authority.nf_owned_handoff_destroy(self.fixture_owner);self.fixture_owner=None
OwnedD3DConsumer.__init__=init
OwnedD3DConsumer.present=present
OwnedD3DConsumer.close=close
