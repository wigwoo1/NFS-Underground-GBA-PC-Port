"""Measure retained native bounds against continuous road geometry at the captured target."""
from pathlib import Path
import ctypes as C,csv,json,hashlib,sys
import numpy as np
from PIL import Image
p=Path('work/camera').resolve()
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
index=int(sys.argv[1]) if len(sys.argv)>1 else 9;assert 0<=index<12
source=list(csv.DictReader((p/'road-attribute-motion-sources.csv').open()))[index]
poses={int(r['role']):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in csv.DictReader((p/'road-attribute-motion-cameras.csv').open()) if int(r['index'])==index}
camera=(Pose*2)(poses[0],poses[1]);alpha=float(source['alpha'])
assert abs(float(source['target'])-(float(source['older_refresh'])+(float(source['newer_refresh'])-float(source['older_refresh']))*alpha))<1e-8
packet=(p/(f'visibility-transition-{index:03}.packet' if len(sys.argv)>1 else 'road-transition-live.packet')).read_bytes();owned=C.create_string_buffer(packet)
d=C.CDLL(str(p/'road-transition-gpu-probe.dll'));d.nf_road_transition_gpu_init.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p];d.nf_road_transition_gpu_render.argtypes=[C.c_void_p,C.c_double,C.c_int,C.c_void_p,C.c_void_p]
assert d.nf_road_transition_gpu_init(owned,len(packet),str(p/'road-correction-reciprocal.bin').encode())==0
captured_alpha=C.c_double();assert d.nf_road_transition_gpu_capture_alpha(C.byref(captured_alpha));assert abs(captured_alpha.value-alpha)<1e-10, 'Packet and retained camera target differ'
native_camera=(Pose*2)();assert d.nf_road_transition_gpu_native_camera(native_camera)
motion=C.CDLL(str(p/'visibility-probe-wide.dll'));motion.nf_pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p]
sampled=Pose();assert motion.nf_pose_sample(C.byref(camera[0]),C.byref(camera[1]),alpha,C.byref(sampled))
position_delta=sum((getattr(sampled.position,k)-getattr(native_camera[0].position,k))**2 for k in 'xyz')**.5
rgb=np.empty((2160,3840,3),np.uint8);depth=np.empty((2160,3840),np.float32);cases=[]
try:
 assert d.nf_road_transition_gpu_uv_mode(2)
 for ring in (-1,0,1,2):
  assert d.nf_road_transition_gpu_select(ring)
  images=[];masks=[];depths=[]
  for bounds in (0,1):
   assert d.nf_road_transition_gpu_render(camera,alpha,bounds,rgb.ctypes.data,depth.ctypes.data)==0
   assert np.isfinite(depth).all()
   images.append(rgb.copy());masks.append(depth>0);depths.append(depth.copy())
  missing=masks[0]&~masks[1];added=masks[1]&~masks[0];both=masks[0]&masks[1]
  delta=np.abs(depths[0][both].astype(np.float64)-depths[1][both]);ys,xs=np.nonzero(missing)
  rect=None
  if ring>=0:
   rect_buffer=(C.c_uint16*4)();assert d.nf_road_transition_gpu_bounds(ring,rect_buffer);rect=list(rect_buffer)
  # Bounding a surface must not produce substantial coverage outside its
  # unclipped raster. Tiny edge rasterization differences are measured too.
  cases.append(dict(ring=ring,unbounded_pixels=int(masks[0].sum()),bounded_pixels=int(masks[1].sum()),removed_pixels=int(missing.sum()),added_pixels=int(added.sum()),changed_rgb_where_both=int((both&np.any(images[0]!=images[1],axis=2)).sum()),changed_depth_where_both=int((both&(depths[0]!=depths[1])).sum()),image_hashes=[hashlib.sha256(im.tobytes()).hexdigest() for im in images]))
  cases[-1].update(native_bounds=rect,removed_pixel_bbox_gl=[int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())] if len(xs) else None,depth_absolute_difference_p95=float(np.quantile(delta,.95)) if len(delta) else 0,depth_absolute_difference_max=float(delta.max()) if len(delta) else 0)
  assert d.nf_road_transition_gpu_render(native_camera,0,1,rgb.ctypes.data,depth.ctypes.data)==0
  native_mask=depth>0
  cases[-1].update(native_camera_bounded_pixels=int(native_mask.sum()),camera_change_coverage_pixels=int(np.count_nonzero(native_mask!=masks[1])),camera_change_rgb_pixels=int(np.any(rgb!=images[1],axis=2).sum()))
  if ring==-1:
   marked=images[1].copy();marked[missing]=(255,0,255);marked[added]=(0,255,0)
   Image.fromarray(np.concatenate([images[0],images[1],marked],axis=1)[::-1]).resize((1920,360)).save(p/(f'road-visibility-alignment-{index:03}.png' if len(sys.argv)>1 else 'road-visibility-alignment.png'))
finally:d.nf_road_transition_gpu_close()
report=dict(result='PASS',measurement_only=True,capture_index=index,target_refresh=float(source['target']),alpha=alpha,continuous_to_native_camera_position_difference=position_delta,rendered_4K_cases=12,cases=cases,scope='Actual retained capture road textures/world/projection/native bounds, continuous source camera and shared near-UV policy. Native-camera variant holds same assets/material/bounds. Measures bounding and camera effects; removed coverage may be intended original visibility. Does not prove bounds are wrong, verify wall/model visibility, original raster parity, dynamic bounds between captured targets or whole-scene smooth60fps.')
(p/(f'road-visibility-alignment-{index:03}-tests.json' if len(sys.argv)>1 else 'road-visibility-alignment-tests.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
