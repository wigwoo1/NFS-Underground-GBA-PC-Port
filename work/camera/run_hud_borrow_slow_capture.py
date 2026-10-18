import ctypes as C,struct
import owned_slow_hud_capture as capture_module
from owned_segmented_frame_candidate import SegmentedFrame
BaseCapture=capture_module.SlowHudCapture
class SegmentedSlowHudCapture(BaseCapture):
 def add(self,metadata,value,sky,profile):
  frame,camera,models,bounds,detail=value
  if isinstance(frame,SegmentedFrame):
   h=struct.unpack_from('<6I2Q',frame.prefix);identity=(h[6],h[1])
   if identity in self.identities:return False
   size=len(frame)+C.sizeof(camera)+C.sizeof(models)+C.sizeof(bounds)+len(sky.lower)+len(sky.upper)
   if len(self.records)>=self.limit or self.bytes+size>self.budget:self.rejected+=1;return False
   value=(bytes(frame),camera,models,bounds,detail)
  return super().add(metadata,value,sky,profile)
capture_module.SlowHudCapture=SegmentedSlowHudCapture
"""Isolated optimized4K HUD visual reuse with retained hit/miss diagnostics."""
import runpy
from pathlib import Path
original_read=Path.read_text;target=Path('work/camera/run_segmented_wait_profile_candidate.py').resolve()
def read(path,*args,**kwargs):
 source=original_read(path,*args,**kwargs)
 if path.resolve()==target:
  assert source.count('owned-gpu-segmented-source-candidate.dll')==1
  source=source.replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-hud-borrow-candidate.dll')
  marker=" path=Path('work/camera/prototype-runs')";assert source.count(marker)==1
  source=source.replace('NativeBatchWorker.queued_draw_probe_enabled=True','NativeBatchWorker.queued_draw_probe_enabled=True\nNativeBatchWorker.slow_hud_capture_ns=5_000_000')
  source=source.replace(marker," stats=(C.c_uint64*2)();gpu.nf_hud_visual_cache_stats.argtypes=[C.c_void_p];assert gpu.nf_hud_visual_cache_stats(stats)\n"+marker)
  source=source.replace(marker," gpu.nf_hud_cpu_profile_count.restype=C.c_uint;gpu.nf_hud_cpu_profile_read.argtypes=[C.c_void_p,C.c_uint];count=gpu.nf_hud_cpu_profile_count();cpurows=(C.c_uint64*(count*11))();assert gpu.nf_hud_cpu_profile_read(cpurows,count);hud_cpu_profile=dict(columns=['epoch','refresh','reuse','has_text','lookup_wall_ns','lookup_cycles','prepare_wall_ns','prepare_cycles','prepare_thread_100ns','candidate_builds','ok'],records=[list(cpurows[i*11:(i+1)*11]) for i in range(count)],dropped=gpu.nf_hud_cpu_profile_dropped())\n"+marker)
  source=source.replace(marker," view_stats=(C.c_uint64*3)();gpu.nf_hud_view_stats.argtypes=[C.c_void_p];assert gpu.nf_hud_view_stats(view_stats) and view_stats[2]==0\n"+marker)
  source=source.replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),hud_visual_cache_stats=list(stats),hud_cpu_profile=hud_cpu_profile,hud_view_stats=list(view_stats))')
 return source
Path.read_text=read
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
