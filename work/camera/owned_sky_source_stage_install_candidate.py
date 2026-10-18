import ctypes as C
import owned_native_source_sky_pan_worker_candidate as module
Base=module.NativeSourceSession
class ProfiledSession(Base):
 def prepare(self,*args,**kwargs):
  row=super().prepare(*args,**kwargs)
  stages=(C.c_uint64*3)();self.source.nf_owned_gpu_sky_draw_stages.argtypes=[C.c_void_p]
  assert self.source.nf_owned_gpu_sky_draw_stages(stages)==0
  row['native_source_stages_ns']=dict(sky=stages[0],world=stages[1],finish=stages[2])
  callback=(C.c_uint64*4)();self.source.nf_owned_gpu_callback_profile.argtypes=[C.c_void_p];assert self.source.nf_owned_gpu_callback_profile(callback)==0
  assert callback[0]<=callback[1]<=callback[2]<=callback[3]
  row['native_callback_profile_ns']=list(callback)
  cache=(C.c_uint64*3)();self.source.nf_owned_decoded_texture_stats.argtypes=[C.c_void_p];self.source.nf_owned_decoded_texture_stats(cache)
  row['native_decoded_cache']=dict(hits=cache[0],misses=cache[1],bytes=cache[2])
  return row
module.NativeSourceSession=ProfiledSession
