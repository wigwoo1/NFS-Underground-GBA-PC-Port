"""Native session boundary for live sampler integration; preserves caller clock."""
import ctypes as C,time
from pathlib import Path
from owned_source_d3d_sky_pan_candidate import OwnedD3DConsumer
from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
class NativeSourceSession:
 def __init__(self):
  self.closed=False;self.pending=None;self.hud_snapshots=[];self.consumer=OwnedD3DConsumer();self.source=C.CDLL(str((Path(__file__).parent/'owned-gpu-source-hud-lease-candidate.dll').resolve()))
  s=self.source;s.nf_source_initialize.argtypes=[C.c_void_p];s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];s.nf_source_packets_publish.argtypes=[C.c_void_p]
  s.nf_owned_gpu_source_segmented_callback.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
  try:self.consumer.bind_window();assert s.nf_source_initialize(self.consumer.window)==0
  except BaseException:self.consumer.close();raise
 def prepare(self,owned,epoch,generation,index):
  assert not self.closed
  if self.pending is not None:raise NativeFrameIdentityError('Native frame already pending')
  s=self.source;assert s.nf_source_packets_begin(epoch,generation,index)==0
  try:
   source_begin=time.perf_counter_ns();hud_profile=None
   if getattr(owned,'segmented',False):
    from owned_hud_renderer_binding_candidate import HudFrameSnapshot
    snapshot=next((x for x in self.hud_snapshots if x._base is owned.frame.base),None);snapshot_begin=time.perf_counter_ns();snapshot_new=snapshot is None
    if snapshot is None:
     if len(self.hud_snapshots)>=2:self.hud_snapshots.pop(0).close()
     snapshot=HudFrameSnapshot(owned.frame.base,library='owned-gpu-source-hud-lease-candidate.dll');self.hud_snapshots.append(snapshot)
    snapshot_end=time.perf_counter_ns()
    s.nf_owned_gpu_source_segmented_hud_callback.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint64,C.c_uint64]
    bind_begin=time.perf_counter_ns()
    with snapshot.bind(owned.frame) as lease:
     callback_begin=time.perf_counter_ns()
     status=s.nf_owned_gpu_source_segmented_hud_callback(C.byref(owned.context),owned.prefix_bytes,owned.tail_pointer,owned.tail_bytes,lease.token,lease.epoch)
     callback_end=time.perf_counter_ns()
    release_end=time.perf_counter_ns()
    hud_profile=dict(snapshot_new=snapshot_new,snapshot_begin_ns=snapshot_begin,snapshot_end_ns=snapshot_end,bind_begin_ns=bind_begin,callback_begin_ns=callback_begin,callback_end_ns=callback_end,release_end_ns=release_end)
   else:status=s.nf_owned_gpu_source_context_callback(C.byref(owned.context))
   assert status==0,status
   source_end=time.perf_counter_ns()
   publication=(C.c_uint64*7)();assert s.nf_source_packets_publish(publication)==0;assert list(publication[:3])==[epoch,generation,index]
   assert self.consumer.render(s,readback=False) is None
   self.pending=(epoch,generation,index);return dict(hud_lease_stages=hud_profile,publication=list(publication),source_prepare_ns=source_end-source_begin,consumer_stages=self.consumer.stage_profile,texture_cache=dict(uploads=self.consumer.texture_uploads,reuses=self.consumer.texture_reuses,bytes=self.consumer.texture_cache_bytes))
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
  try:
   for snapshot in self.hud_snapshots:snapshot.close()
   self.hud_snapshots=[]
   assert self.source.nf_owned_gpu_close()
  finally:self.consumer.close();self.pending=None;self.closed=True

