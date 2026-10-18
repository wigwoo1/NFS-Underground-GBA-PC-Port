"""Fullscene source activation sampling with exact original endpoint pixels."""
import runpy,ctypes as C,struct
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_activation_scenery_record_pairs.py');frames=v['v']['frames'];scenes=v['scenes'];rom=v['v']['rom'];table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);old_roads,_=history.plan(scenes[0].graph)
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);prepared=None;counts=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,old_roads,rom)
 for alpha in (0,.1,.25,.5,.6,.6666666667,.75,.9,.99,1):
  frame,camera,models,bounds,detail=prepared.sample(alpha);count=sum(row['kind']==3 for row in records(frame)['records']);counts.append((alpha,count))
  if alpha in (0,1):
   reference=frames[int(alpha)];assert d.nf_owned_gpu_draw(reference,len(reference))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
   assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
   if rgb.raw!=expected:
    import numpy as np
    changed=int(np.count_nonzero(np.any(np.frombuffer(rgb.raw,dtype=np.uint8).reshape(-1,3)!=np.frombuffer(expected,dtype=np.uint8).reshape(-1,3),axis=1)))
    raise AssertionError(f'Endpoint alpha={alpha} differs at {changed} pixels; original/assembled geometry records {len(records(reference)["records"])}/{len(records(frame)["records"])}')
  else:assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,len(records(frame)['records']))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
 assert counts[0][1]==1 and counts[-1][1]==6
 print('PASS: model activation fullscene endpoints pixel exact, eight fractional 4K renders',counts,prepared.pair._scenery_activation)
finally:
 if prepared:prepared.close()
 history.close();assert d.nf_owned_gpu_close()
