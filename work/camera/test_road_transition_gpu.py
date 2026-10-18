"""Actual captured-road textures and shared 4K GPU path at a clipping boundary."""
from pathlib import Path
import ctypes as C,csv,json,os,hashlib
import numpy as np
from PIL import Image
p=Path('work/camera').resolve();os.environ['NF_ROAD_RECIPROCAL']=str(p/'road-correction-reciprocal.bin')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'road-attribute-motion-cameras.csv').open())}
sources=list(csv.DictReader((p/'road-attribute-motion-sources.csv').open()));segments={}
for i,row in enumerate(sources):segments[(int(row['older_refresh']),int(row['newer_refresh']))]=(poses[i,0],poses[i,1])
edge=next(r for r in csv.DictReader((p/'road-attribute-motion-edges.csv').open()) if int(r['index'])==9 and int(r['identity'])==10038408689761076994 and int(r['edge'])==1)
world=(Point*2)(*[Point(*[float(edge[f'world{n}'+k]) for k in 'xyz']) for n in (0,1)])
motion=C.CDLL(str(p/'visibility-probe-wide.dll'));sample=motion.nf_rigid_scene_sample;sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p];fixed=Pose(Point(0,0,0),Quaternion(0,0,0,1))
def pair_at(target):
 key=next(k for k in sorted(segments) if k[0]<=target<=k[1]);return (Pose*2)(*segments[key]),(target-key[0])/(key[1]-key[0])
def depth_at(target):
 camera,alpha=pair_at(target);out=(Point*2)();assert sample(C.byref(camera[0]),C.byref(camera[1]),C.byref(fixed),C.byref(fixed),alpha,world,2,out);return out[1].z
lo,hi=[float(sources[i]['target']) for i in (9,10)];assert depth_at(lo)>64 and depth_at(hi)<64
for _ in range(45):
 mid=(lo+hi)/2
 if depth_at(mid)>64:lo=mid
 else:hi=mid
root=(lo+hi)/2;assert abs(depth_at(root)-64)<1e-8
gpu=C.CDLL(str(p/'road-transition-gpu-probe.dll'));gpu.nf_road_transition_gpu_init.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p];gpu.nf_road_transition_gpu_render.argtypes=[C.c_void_p,C.c_double,C.c_int,C.c_void_p,C.c_void_p]
packet=(p/'road-transition-live.packet').read_bytes();owned=C.create_string_buffer(packet);initialized=gpu.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode());assert initialized==0,initialized
rgb=np.empty((2160,3840,3),dtype=np.uint8);depth=np.empty((2160,3840),dtype=np.float32)
cases=[];comparisons=[];isolated=[];uv_experiments=[];endpoint_comparisons=[];cutoff_comparisons=[]
try:
 for bounds in (0,1):
  previous=None;near_images=[]
  for offset in (-1e-4,-1e-6,-1e-8,0,1e-8,1e-6,1e-4):
   camera,alpha=pair_at(root+offset);assert gpu.nf_road_transition_gpu_render(camera,alpha,bounds,rgb.ctypes.data,depth.ctypes.data)==0
   mask=depth>0;assert mask.any() and np.isfinite(depth).all()
   cases.append(dict(bounds=bounds,refresh_offset=offset,covered_pixels=int(mask.sum()),image_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
   if previous is not None:comparisons.append(dict(bounds=bounds,offset_pair=[previous[0],offset],changed_rgb_pixels=int(np.any(previous[1]!=rgb,axis=2).sum()),changed_coverage_pixels=int(np.count_nonzero(previous[2]!=mask))))
   if offset in (-1e-8,0,1e-8):near_images.append(rgb.copy())
   previous=(offset,rgb.copy(),mask.copy())
  # Retain actual diagnostic render, flipped from GL bottom-up layout.
  Image.fromarray(np.concatenate(near_images,axis=1)[::-1]).resize((1920,360)).save(p/f'road-transition-gpu-bounds{bounds}.png')
 for ring in sorted({int(r['ring']) for r in csv.DictReader((p/'road-attribute-motion-edges.csv').open()) if int(r['index'])==9}):
  assert gpu.nf_road_transition_gpu_select(ring)
  images=[];masks=[]
  for offset in (-1e-8,1e-8):
   camera,alpha=pair_at(root+offset);assert gpu.nf_road_transition_gpu_render(camera,alpha,0,rgb.ctypes.data,depth.ctypes.data)==0
   images.append(rgb.copy());masks.append(depth>0)
  isolated.append(dict(ring=ring,covered_pixels=[int(m.sum()) for m in masks],changed_rgb_pixels=int(np.any(images[0]!=images[1],axis=2).sum()),changed_coverage_pixels=int(np.count_nonzero(masks[0]!=masks[1]))))
 for mode in (1,2):
  assert gpu.nf_road_transition_gpu_uv_mode(mode)
  for ring in (-1,0,1,2):
   assert gpu.nf_road_transition_gpu_select(ring)
   images=[];masks=[]
   for offset in (-1e-8,1e-8):
    camera,alpha=pair_at(root+offset);assert gpu.nf_road_transition_gpu_render(camera,alpha,0,rgb.ctypes.data,depth.ctypes.data)==0
    images.append(rgb.copy());masks.append(depth>0)
   uv_experiments.append(dict(mode=mode,ring=ring,changed_rgb_pixels=int(np.any(images[0]!=images[1],axis=2).sum()),changed_coverage_pixels=int(np.count_nonzero(masks[0]!=masks[1]))))
 assert gpu.nf_road_transition_gpu_select(-1)
 for target in sorted({v for key in segments for v in key}):
  images=[]
  for mode in (0,2):
   assert gpu.nf_road_transition_gpu_uv_mode(mode);camera,alpha=pair_at(target);assert gpu.nf_road_transition_gpu_render(camera,alpha,0,rgb.ctypes.data,depth.ctypes.data)==0;images.append(rgb.copy())
  changed=int(np.any(images[0]!=images[1],axis=2).sum());endpoint_comparisons.append(dict(target=target,changed_rgb_pixels=changed))
 # Measure continuity at the new blend cutoff as well as the original plane.
 lo,hi=[float(sources[i]['target']) for i in (9,10)]
 for _ in range(45):
  mid=(lo+hi)/2
  if depth_at(mid)>65:lo=mid
  else:hi=mid
 cutoff=(lo+hi)/2;assert abs(depth_at(cutoff)-65)<1e-8
 for mode in (0,2):
  assert gpu.nf_road_transition_gpu_uv_mode(mode);images=[]
  for offset in (-1e-8,1e-8):
   camera,alpha=pair_at(cutoff+offset);assert gpu.nf_road_transition_gpu_render(camera,alpha,0,rgb.ctypes.data,depth.ctypes.data)==0;images.append(rgb.copy())
  cutoff_comparisons.append(dict(mode=mode,target=cutoff,changed_rgb_pixels=int(np.any(images[0]!=images[1],axis=2).sum())))
finally:gpu.nf_road_transition_gpu_close()
report=dict(result='PASS',measurement_only=True,texture_boundary_continuity_verified=False,captured_packet_bytes=len(packet),boundary_target_refresh=root,boundary_depth=depth_at(root),rendered_4K_cases=len(cases)+2*len(isolated),cases=cases,comparisons=comparisons,isolated_ring_boundary_changes=isolated,scope='Measurement PASS; texture continuity fails at sampled topology boundary. Actual retained road geometry/projection/indices/RGBA/source UVs through shared corrected clipping/triangulation/GPU shader. Roads only, frame9 material/native bounds held fixed. No original raster fidelity, dynamic bound correctness, whole-scene continuity, scanout or smooth60fps proof.')
report['diagnostic_uv_experiments']=uv_experiments
report['rendered_4K_cases']+=2*len(uv_experiments)
report['captured_source_endpoint_mode2_comparisons']=endpoint_comparisons
report['mode2_cutoff_comparisons']=cutoff_comparisons
report['rendered_4K_cases']+=2*len(endpoint_comparisons)+4
report['diagnostic_uv_scope']='Probe-only mode1 reverts to geometric source UVs; mode2 blends generated UV to front corner within depth64..65. Both retain shared triangulation. Mode1 loses original clipping sampling agreement; mode2 changes original front-on-plane UV endpoint. Neither is enabled live or verified for fidelity.'
(p/'road-transition-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
