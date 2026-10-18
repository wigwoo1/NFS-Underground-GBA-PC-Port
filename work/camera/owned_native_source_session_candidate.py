"""Native session boundary for live sampler integration; preserves caller clock."""
import ctypes as C
from pathlib import Path
from owned_source_d3d_present_consumer_candidate import OwnedD3DConsumer
class NativeSourceSession:
 def __init__(self):
  self.closed=False;self.consumer=OwnedD3DConsumer();self.source=C.CDLL(str((Path(__file__).parent/'owned-gpu-source-context-free-candidate.dll').resolve()))
  s=self.source;s.nf_source_initialize.argtypes=[C.c_void_p];s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];s.nf_source_packets_publish.argtypes=[C.c_void_p]
  try:self.consumer.bind_window();assert s.nf_source_initialize(self.consumer.window)==0
  except BaseException:self.consumer.close();raise
 def draw(self,owned,epoch,generation,index):
  assert not self.closed;s=self.source;assert s.nf_source_packets_begin(epoch,generation,index)==0
  try:
   status=s.nf_owned_gpu_source_context_callback(C.byref(owned.context));assert status==0,status
   publication=(C.c_uint64*7)();assert s.nf_source_packets_publish(publication)==0;assert list(publication[:3])==[epoch,generation,index]
   assert self.consumer.render(s,readback=False) is None
   return dict(publication=list(publication),presentation=self.consumer.present())
  finally:assert s.nf_source_packets_close()==0
 def close(self):
  if self.closed:return
  try:assert self.source.nf_owned_gpu_close()
  finally:self.consumer.close();self.closed=True
