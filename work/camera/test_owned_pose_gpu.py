from pathlib import Path
import ctypes as C,json,hashlib
from sample_owned_motion import sample
p=Path('work/camera');refs=[8758,8762,8766,8769,8773,8776,8780];d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_poses.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 for older,newer in zip(refs,refs[1:]):
  a=(p/'motion-actual-scanline-assets'/f'{older}-native-complete-frame.bin').read_bytes();b=(p/'motion-actual-scanline-assets'/f'{newer}-native-complete-frame.bin').read_bytes();images={}
  for alpha in (0,.25,.5,.75,1):
   frame,cm,models=sample(a,b,alpha)
   if cm is None:assert d.nf_owned_gpu_draw(frame,len(frame))==0
   else:assert d.nf_owned_gpu_draw_poses(frame,len(frame),cm,models,len(models)//12)==0
   assert d.nf_owned_gpu_read(rgb,len(rgb))==0;images[alpha]=rgb.raw
  assert images[0]==(p/f'owned-timed-{older}.ppm').read_bytes().split(b'\n',3)[3];assert images[1]==(p/f'owned-timed-{newer}.ppm').read_bytes().split(b'\n',3)[3]
  assert len({hashlib.sha256(v).hexdigest() for v in images.values()})==5
  checks.append(dict(older=older,newer=newer,exact_endpoints=2,distinct_intermediates=3,hashes={str(k):hashlib.sha256(v).hexdigest() for k,v in images.items()}))
 # Invalid pose must not modify the retained GPU target.
 frame,cm,models=sample(a,b,.5);cm[0]=float('nan');assert d.nf_owned_gpu_draw_poses(frame,len(frame),cm,models,len(models)//12)==37
 assert d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==images[1]
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_RAW_POSE_INTERMEDIATE_GPU',exact_endpoint_frames=12,distinct_intermediate_frames=18,checks=checks,invalid_pose_target_unchanged=True,scope='Six scene pairs3840x2160 diagnostic including source visibility changes. Sampled model winding/viewport rejection; source scissor/material/HUD and scene membership retained between endpoints; no60Hzscheduler/fullscene motion fidelity proof.')
(p/'owned-pose-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
