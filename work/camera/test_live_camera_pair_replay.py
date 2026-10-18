"""Compare retained source camera-pair sampling to actual presented camera."""
from pathlib import Path
import csv,ctypes as C,json,sys
p=Path('work/camera')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
lib=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));sample=lib.nf_pose_sample;sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p]
transform=lib.nf_rigid_scene_sample;transform.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
source=list(csv.DictReader((p/'road-attribute-motion-sources.csv').open()));pose_rows=list(csv.DictReader((p/'road-attribute-motion-cameras.csv').open()));assert len(source)==12 and len(pose_rows)==36
poses={(int(r['index']),int(r['role'])):Pose(Point(*[float(r[k]) for k in 'xyz']),Quaternion(*[float(r['q'+k]) for k in 'xyzw'])) for r in pose_rows}
known={};position=rotation=endpoint_error=source_error=0.;shared=endpoint_checks=0
fixed=Pose(Point(0,0,0),Quaternion(0,0,0,1))
for i,row in enumerate(source):
 for role,key in ((0,'older'),(1,'newer')):
  identity=(int(row['epoch']),int(row[key]));raw=bytes(poses[i,role])
  if identity in known:assert known[identity]==raw;shared+=1
  else:known[identity]=raw
 sampled=Pose();assert sample(C.byref(poses[i,0]),C.byref(poses[i,1]),float(row['alpha']),C.byref(sampled))
 for alpha in (0,1):
  endpoint=Pose();assert sample(C.byref(poses[i,0]),C.byref(poses[i,1]),alpha,C.byref(endpoint))
  expected=poses[i,alpha]
  assert max(abs(getattr(endpoint.position,k)-getattr(expected.position,k)) for k in 'xyz')<1e-12
  assert min(max(abs(getattr(endpoint.rotation,k)-sign*getattr(expected.rotation,k)) for k in 'xyzw') for sign in (-1,1))<1e-12
  endpoint_checks+=1
 position=max(position,max(abs(getattr(sampled.position,k)-getattr(poses[i,2].position,k)) for k in 'xyz'))
 rotation=max(rotation,min(max(abs(getattr(sampled.rotation,k)-sign*getattr(poses[i,2].rotation,k)) for k in 'xyzw') for sign in (-1,1)))
for edge in csv.DictReader((p/'road-attribute-motion-edges.csv').open()):
 i=int(edge['index']);world=(Point*2)(*[Point(*[float(edge[f'world{n}'+k]) for k in 'xyz']) for n in (0,1)])
 actual=(Point*2)();interpolated=(Point*2)()
 assert transform(C.byref(poses[i,2]),C.byref(poses[i,2]),C.byref(fixed),C.byref(fixed),0,world,2,actual)
 assert transform(C.byref(poses[i,0]),C.byref(poses[i,1]),C.byref(fixed),C.byref(fixed),float(source[i]['alpha']),world,2,interpolated)
 for n in (0,1):
  endpoint_error=max(endpoint_error,max(abs(getattr(actual[n],k)-float(edge[f'camera{n}'+k])) for k in 'xyz'))
  source_error=max(source_error,max(abs(getattr(interpolated[n],k)-float(edge[f'camera{n}'+k])) for k in 'xyz'))
assert endpoint_error<1e-9
if '--continuous' in sys.argv:
 assert position<1e-9 and rotation<1e-12 and source_error<1e-9
report=dict(result='PASS',captured_frames=12,unique_source_cameras=len(known),reused_source_camera_identity_checks=shared,maximum_source_sample_position_difference=position,maximum_source_sample_quaternion_difference=rotation,maximum_source_sample_camera_vertex_difference=source_error,maximum_presented_camera_vertex_reconstruction_error=endpoint_error,source_pair_reconstructs_presented_geometry=source_error<1e-9,scope='Retains original source camera pair and actual generated presented camera separately; verifies repeated source identities and measures interpolation versus generated geometry. A mismatch means source-pair interpolation alone cannot replay live generator; no GPU/fullscene fidelity or gameplay timing proof.')
(p/'live-camera-pair-replay-tests.json').write_text(json.dumps(report,indent=2));print(report)
report['exact_source_endpoint_checks']=endpoint_checks
report['continuous_required']='--continuous' in sys.argv
if '--continuous' in sys.argv:report['scope']='Opt-in live continuous camera reconstructs captured world edges from original source pair within numerical rounding and retains exact source endpoint poses. Native quantized visibility/bounds and object generation unchanged; no fullscene raster or smooth60fps proof.'
(p/'live-camera-pair-replay-tests.json').write_text(json.dumps(report,indent=2))
if '--continuous' in sys.argv:(p/'live-continuous-camera-replay-tests.json').write_text(json.dumps(report,indent=2))
