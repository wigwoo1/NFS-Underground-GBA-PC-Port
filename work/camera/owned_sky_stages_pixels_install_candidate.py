import os
capture_begin=int(os.environ.get("NF_SKY_CAPTURE_BEGIN","120"))
assert 1<=capture_begin<=2000
import ctypes as C,types,numpy as np,time
from pathlib import Path
import owned_sky_linear_pixels_install_candidate as pixels
from owned_ordered_render_tail_binding_candidate import Tail,address
from owned_uncovered_window_candidate import OwnedD3DConsumer
target=pixels.original_render
while "ordered_tail" not in target.__globals__:target=target.__globals__["original"]
original=target.__globals__["ordered_tail"]
bridge=C.CDLL(str(Path("work/camera/ordered-render-tail-stages-diagnostic-candidate.dll").resolve()))
bridge.nf_ordered_render_tail_stages.argtypes=[C.POINTER(Tail),C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
buffers=[C.create_string_buffer(3840*2160*4) for _ in range(3)]
count=0
def ordered_tail(self,s,vertices,nv,offsets,ids,states,nd):
 global count
 count+=1
 if not capture_begin<=count<capture_begin+16:return original(self,s,vertices,nv,offsets,ids,states,nd)
 d=self.d
 job=Tail(address(d.nf_d3d_source_sky_pan_batch),address(d.nf_d3d_world_batch),address(d.nf_d3d_source_hud_batch),address(s.nf_source_sky_info),address(s.nf_source_sky_copy),address(s.nf_source_hud_planes_info),address(s.nf_source_hud_plane_copy),address(s.nf_source_hud_batches_count),address(s.nf_source_hud_batches_copy),vertices.ctypes.data,nv,vertices.nbytes,C.addressof(offsets),(nd+1)*4,C.addressof(ids),nd*4,C.addressof(states),nd,nd*72)
 failed=C.c_uint()
 begin=time.perf_counter_ns()
 result=bridge.nf_ordered_render_tail_stages(C.byref(job),C.sizeof(job),C.byref(failed),address(d.nf_d3d_read),*buffers)
 assert result==0,(result,failed.value)
 bands=[np.frombuffer(buf,np.uint8).reshape(2160,3840,4)[594:1458:27,300:3540].copy() for buf in buffers]
 np.savez_compressed(pixels.folder/("stages-"+str(count-capture_begin)+".npz"),sky=bands[0],world=bands[1],hud=bands[2])
 if count==capture_begin:
  from PIL import Image
  for name,buf in zip(("sky","world","hud"),buffers):
   Image.fromarray(np.frombuffer(buf,np.uint8).reshape(2160,3840,4)).save(pixels.folder/("full-"+name+".png"))
  np.savez_compressed(pixels.folder/"world-commands.npz",vertices=vertices.copy(),offsets=np.frombuffer(C.string_at(offsets,(nd+1)*4),np.uint32),ids=np.frombuffer(C.string_at(ids,nd*4),np.uint32),states=np.frombuffer(C.string_at(states,nd*72),np.uint8).reshape(nd,72))
 self.ordered_tail_ticks=[1000000000,begin,*([time.perf_counter_ns()]*5)]
 self.ordered_tail_completed=True
target.__globals__["ordered_tail"]=ordered_tail
