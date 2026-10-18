"""Native session boundary for live sampler integration; preserves caller clock."""
import ctypes as C,time
from pathlib import Path
from owned_source_d3d_fixed_quads_consumer_candidate import OwnedD3DConsumer
class NativeFrameIdentityError(ValueError):pass
class NativeSourceSession:
 def __init__(self):
  self.closed=False;self.pending=None;self.consumer=OwnedD3DConsumer();self.source=C.CDLL(str((Path(__file__).parent/'owned-gpu-source-context-free-candidate.dll').resolve()))
  s=self.source;s.nf_source_initialize.argtypes=[C.c_void_p];s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];s.nf_source_packets_publish.argtypes=[C.c_void_p]
  try:self.consumer.bind_window();assert s.nf_source_initialize(self.consumer.window)==0
  except BaseException:self.consumer.close();raise
 def prepare(self,owned,epoch,generation,index):
  assert not self.closed
  if self.pending is not None:raise NativeFrameIdentityError('Native frame already pending')
  s=self.source;assert s.nf_source_packets_begin(epoch,generation,index)==0
  try:
   source_begin=time.perf_counter_ns()
   status=s.nf_owned_gpu_source_context_callback(C.byref(owned.context));assert status==0,status
   source_end=time.perf_counter_ns()
   publication=(C.c_uint64*7)();assert s.nf_source_packets_publish(publication)==0;assert list(publication[:3])==[epoch,generation,index]
   assert self.consumer.render(s,readback=False) is None
   self.pending=(epoch,generation,index);return dict(publication=list(publication),source_prepare_ns=source_end-source_begin,consumer_stages=self.consumer.stage_profile,texture_cache=dict(uploads=self.consumer.texture_uploads,reuses=self.consumer.texture_reuses,bytes=self.consumer.texture_cache_bytes))
  finally:assert s.nf_source_packets_close()==0
 def present(self,epoch,generation,index):
  if self.closed or self.pending!=(epoch,generation,index):raise NativeFrameIdentityError('Native frame identity mismatch or unavailable')
  result=self.consumer.present();self.pending=None;return result
 def abort(self,epoch,generation,index):
  if self.closed or self.pending!=(epoch,generation,index):raise NativeFrameIdentityError('Native frame identity mismatch or unavailable')
  self.pending=None
 def draw(self,owned,epoch,generation,index):
  result=self.prepare(owned,epoch,generation,index);result['presentation']=self.present(epoch,generation,index);return result
 def close(self):
  if self.closed:return
  try:assert self.source.nf_owned_gpu_close()
  finally:self.consumer.close();self.pending=None;self.closed=True
