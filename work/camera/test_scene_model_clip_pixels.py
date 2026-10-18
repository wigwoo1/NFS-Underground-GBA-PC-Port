import runpy,ctypes as C,struct,json
from pathlib import Path
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));args=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
gpu.nf_owned_gpu_draw_surface_clips.argtypes=args;gpu.nf_owned_gpu_draw_scene_clips.argtypes=args;gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);changed=[];fractional=[];compatible=0
try:
 for i,(frame,camera,models,bounds,detail) in enumerate(v['samples']):
  if camera is None:
   assert gpu.nf_owned_gpu_draw(frame,len(frame))==0;continue
  rows=records(frame)['records'];integer=(C.c_double*len(bounds))(*bounds)
  for index,row in enumerate(rows):
   if row['kind']==3:
    left,top,right,bottom=struct.unpack('<4i',row['blocks'][9]);integer[index*4:index*4+4]=(left,right,top,bottom)
  count=detail['geometry_records']
  assert gpu.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,count)==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;old=rgb.raw
  assert gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,integer,count)==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==old,i;compatible+=1
  if bytes(integer)!=bytes(bounds):
   fractional.append(i)
   assert gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,count)==0
   assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
   if rgb.raw!=old:changed.append(i)
 result=dict(integer_compatible_samples=compatible,fractional_samples=fractional,changed_fractional_images=changed,scope='native4K pixel comparisons; isolated scene replay, not live timing')
 Path('work/camera/prototype-runs/scene-model-clip-pixels.json').write_text(json.dumps(result,indent=2));print(result)
finally:gpu.nf_owned_gpu_close()
