"""Bounded final sky-band pixels; install after all consumer setup."""
import ctypes as C,json,time
from pathlib import Path
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.render
folder=Path('work/camera/prototype-runs')/('current-launcher-sky-pixels-'+str(time.time_ns()))
folder.mkdir()
rows=[]
count=0
def render(self,source,*args,**kwargs):
 global count
 count+=1
 if not hasattr(self,'_sky_capture_callback'):
  native=self.d.nf_d3d_source_sky_pan_batch
  native.argtypes=[C.c_void_p,C.c_void_p]
  Callback=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)
  def sky(info,copy):
   status=native(info,copy)
   if status:return status
   if 120<=count<152:
    try:
     rgba=C.create_string_buffer(3840*2160*4)
     self.d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
     read_status=self.d.nf_d3d_read(rgba,len(rgba))
     if read_status:return 90+read_status
     (folder/(str(len(rows))+'.sky-stage.rgba')).write_bytes(C.string_at(C.addressof(rgba)+594*3840*4,64*3840*4))
    except BaseException as error:
     print('SKY_STAGE_CAPTURE_ERROR',repr(error),flush=True)
     return 99
   return 0
  self._sky_capture_native=native
  self._sky_capture_callback=Callback(sky)
  self.d.nf_d3d_source_sky_pan_batch=self._sky_capture_callback
 if not hasattr(self,'_world_capture_callback'):
  native_world=self.d.nf_d3d_world_batch
  types=[C.c_void_p,C.c_uint,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_size_t]
  native_world.argtypes=types
  World=C.CFUNCTYPE(C.c_int,*types)
  def world(*values):
   status=native_world(*values)
   if status:return status
   if 120<=count<152:
    try:
     rgba=C.create_string_buffer(3840*2160*4)
     self.d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
     read_status=self.d.nf_d3d_read(rgba,len(rgba))
     if read_status:return 90+read_status
     (folder/(str(len(rows))+'.world-stage.rgba')).write_bytes(C.string_at(C.addressof(rgba)+594*3840*4,64*3840*4))
    except BaseException as error:
     print('WORLD_STAGE_CAPTURE_ERROR',repr(error),flush=True)
     return 99
   return 0
  self._world_capture_native=native_world
  self._world_capture_callback=World(world)
  self.d.nf_d3d_world_batch=self._world_capture_callback
 result=original(self,source,*args,**kwargs)
 if 120<=count<152:
  publication=(C.c_uint64*7)()
  source.nf_source_packets_publish.argtypes=[C.c_void_p]
  publication_status=source.nf_source_packets_publish(publication)
  self.d.nf_d3d_read.argtypes=[C.c_void_p,C.c_size_t]
  rgba=C.create_string_buffer(3840*2160*4)
  begin=time.perf_counter_ns()
  read_status=self.d.nf_d3d_read(rgba,len(rgba))
  if read_status!=0:raise RuntimeError("Current sky readback status="+str(read_status))
  enabled=(C.c_uint*2)();weights=(C.c_double*2)()
  source.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p]
  sky_status=source.nf_source_sky_info(enabled,weights)
  self.d.nf_d3d_sky_input_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
  for slot in range(2):
   plane=C.create_string_buffer(240*160*4)
   assert self.d.nf_d3d_sky_input_copy(slot,plane,len(plane))==0
   (folder/(str(len(rows))+'.input'+str(slot)+'.rgba')).write_bytes(plane.raw)
  name=str(len(rows))+'.rgba'
  (folder/name).write_bytes(C.string_at(C.addressof(rgba)+594*3840*4,64*3840*4))
  rows.append(dict(publication=list(publication),publication_status=publication_status,draw_number=count,band_y=594,band_height=64,sky_status=sky_status,sky_enabled=list(enabled),sky_weights=list(weights),backend=Path(self.d._name).name,read_begin_ns=begin,read_end_ns=time.perf_counter_ns(),file=name))
 return result
OwnedD3DConsumer.render=render
def save():
 (folder/'manifest.json').write_text(json.dumps(dict(rows=rows,total_draws=count,scope='Final y594:658 band; GPU readback perturbs timing; world/HUD overlap possible; no scanout proof.'),indent=2))
 print('CURRENT_LAUNCHER_SKY_PIXELS',folder,flush=True)





