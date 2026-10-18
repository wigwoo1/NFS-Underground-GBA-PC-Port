import runpy,sys,ctypes as C
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_failed_world_motion.py');data=v['data'];history=EndpointRoadPlanner(v['rom'],data['table']);roads,_=history.plan(v['scenes'][0].graph)
prepared=PreparedWorldMotion(*data['frames'],*v['scenes'],history,roads,v['rom'])
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3)
try:
 for i in range(101):
  alpha=i/100;frame,camera,models,bounds,detail=prepared.sample(alpha)
  code=d.nf_owned_gpu_draw(frame,len(frame)) if alpha in (0,1) else d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
  if code:raise ValueError(('GPU boundary failure',alpha,code,detail))
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0
 print('PASS retained boundary 101 fullscene 4K GPU samples')
finally:prepared.close();history.close();d.nf_owned_gpu_close()
