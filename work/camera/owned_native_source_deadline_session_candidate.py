"""Isolated owner-thread native deadline/commit session; live adapter pending."""
import ctypes as C,time
from pathlib import Path
from owned_native_source_present_profile_session_candidate import NativeSourceSession as Base,NativeFrameIdentityError
class NativeSourceSession(Base):
 def __init__(self):
  super().__init__()
  self.commit_dll=C.CDLL(str((Path(__file__).parent/'owned-native-deadline-present-candidate.dll').resolve()))
  self.commit=self.commit_dll.nf_owned_native_deadline_present
  P=C.c_void_p;U=C.c_uint64
  self.commit.argtypes=[P,U,U,U,U,U,C.c_double,U,P,P,P,P,P]
 def present_at_deadline(self,owner,epoch,generation,older,newer,index,alpha,deadline):
  if self.closed or self.pending!=(epoch,generation,index):raise NativeFrameIdentityError('Native deadline frame identity mismatch')
  d=self.consumer.d;state=(C.c_uint64*7)();out=(C.c_uint64*8)(*[123]*8);wait=(C.c_uint64*4)();stages=(C.c_uint64*7)();status=C.c_int(-999)
  began=time.perf_counter_ns()
  try:
   assert d.nf_d3d_window_pump(self.consumer.window,state)==0
   result=self.commit(owner,epoch,generation,older,newer,index,alpha,deadline,C.cast(d.nf_d3d_present,C.c_void_p),out,wait,stages,C.byref(status))
   assert result in (0,1,-1)
   if result==-1 and status.value!=3:raise RuntimeError(('Native deadline presentation failed',status.value))
   profile=None
   if status.value!=-999:
    values=(C.c_uint64*5)();assert d.nf_d3d_present_profile(values)==0;profile=list(values)
   return dict(native_result=result,commit=list(out),wait=list(wait),stages=list(stages),presentation=dict(status=status.value,window=list(state),native_present_profile=profile),owner_call_begin_ns=began,owner_call_end_ns=time.perf_counter_ns())
  finally:
   # Retired prepared frames cannot be presented again after resume.
   self.pending=None
