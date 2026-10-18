import runpy,ctypes as C,json,math
from pathlib import Path
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_external_fullscene_transition.py')
gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()))
args=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
for name in ('nf_owned_gpu_draw_scene_clips','nf_owned_gpu_draw_surface_clips'):getattr(gpu,name).argtypes=args
gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
frame,camera,models,bounds,detail=v['samples'][35];count=detail['geometry_records']
rows=records(frame)['records'];model_index=next(i for i,r in enumerate(rows) if r['kind']==3)
rgb=C.create_string_buffer(3840*2160*3);passed=[]
def pixels(scene=False):
 fn=gpu.nf_owned_gpu_draw_scene_clips if scene else gpu.nf_owned_gpu_draw_surface_clips
 assert fn(frame,len(frame),camera,models,bounds,count)==0
 assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
 return rgb.raw
try:
 baseline=pixels();exact=pixels(True)
 cases=[('null camera',frame,len(frame),None,models,bounds,count),('null models',frame,len(frame),camera,None,bounds,count),('null bounds',frame,len(frame),camera,models,None,count),('zero count',frame,len(frame),camera,models,bounds,0),('excess count',frame,len(frame),camera,models,bounds,145),('mismatched count',frame,len(frame),camera,models,bounds,count-1),('short frame',frame,39,camera,models,bounds,count)]
 for label,offset,value in [('nan',0,math.nan),('infinity',1,math.inf),('negative left',0,-1),('right outside',1,241),('bottom outside',3,161),('reversed horizontal',0,240),('reversed vertical',2,160)]:
  b=(C.c_double*len(bounds))(*bounds);b[model_index*4+offset]=value
  cases.append((label,frame,len(frame),camera,models,b,count))
 # These reach the delegated pose validator after the model override is enabled.
 for label,original in [('nonfinite camera',camera),('nonfinite model pose',models)]:
  p=(C.c_double*len(original))(*original);p[0]=math.nan
  cases.append((label,frame,len(frame),p if original is camera else camera,p if original is models else models,bounds,count))
 for label,*arguments in cases:
  assert gpu.nf_owned_gpu_draw_scene_clips(*arguments)==37,label
  assert pixels()==baseline,(label,'legacy state leaked')
  assert pixels(True)==exact,(label,'scene recovery mismatch')
  passed.append(label)
 result=dict(rejected_cases=passed,recovery_pixel_parity=True,resolution=[3840,2160],scope='component rejection and state recovery; not live timing')
 Path('work/camera/prototype-runs/scene-model-clip-rejection.json').write_text(json.dumps(result,indent=2));print(result)
finally:gpu.nf_owned_gpu_close()
