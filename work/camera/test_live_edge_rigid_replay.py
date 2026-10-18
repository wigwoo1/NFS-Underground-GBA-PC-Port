"""Retained world edges replayed through the actual rigid presentation helper."""
from pathlib import Path
import ctypes as C,csv,json,math
p=Path('work/camera');edges=list(csv.DictReader((p/'road-attribute-motion-edges.csv').open()))
rows=[r for r in csv.DictReader((p/'road-attribute-live-parity.csv').open()) if int(r['ready'])][180:192];assert len(rows)==12
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
lib=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));sample=lib.nf_rigid_scene_sample;sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
near=C.CDLL(str((p/'road-near-attributes.dll').resolve())).nf_road_near_attributes;near.argtypes=[C.c_double,C.c_double,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_void_p,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes());fixed=Pose(Point(0,0,0),Quaternion(0,0,0,1))
def pose(row):return Pose(Point(*[float(row['camera_'+k]) for k in 'xyz']),Quaternion(*[float(row['camera_q'+k]) for k in 'xyzw']))
poses=[pose(r) for r in rows]
def transform(world,a,b,t):
 out=(Point*2)();assert sample(C.byref(a),C.byref(b),C.byref(fixed),C.byref(fixed),t,world,2,out);return out
maximum=0
for edge in edges:
 i=int(edge['index']);world=(Point*2)(*[Point(*[float(edge[f'world{j}'+k]) for k in 'xyz']) for j in (0,1)])
 out=transform(world,poses[i],poses[i],0)
 for j in (0,1):
  error=max(abs(getattr(out[j],k)-float(edge[f'camera{j}'+k])) for k in 'xyz');maximum=max(maximum,error);assert error<1e-5
 assert float(edge['z0'])==float(edge['camera0z']) and float(edge['z1'])==float(edge['camera1z'])
changes=json.loads((p/'road-attribute-motion-edge-tests.json').read_text())['topology_changes'];bykey={(int(r['index']),int(r['identity']),int(r['edge'])):r for r in edges};samples=clipped=0;roots=[]
for change in changes:
 i,j=change['frame_pair'];edge=bykey[(i,change['identity'],change['edge'])]
 world=(Point*2)(*[Point(*[float(edge[f'world{n}'+k]) for k in 'xyz']) for n in (0,1)])
 raw=(C.c_int32*4)(*[int(edge[k]) for k in ('a0','a1','b0','b1')]);moving=next(k for k in (0,1) if (change['before_depths'][k]<64)!=(change['after_depths'][k]<64))
 for step in range(513):
  out=transform(world,poses[i],poses[j],step/512);samples+=1
  if (out[0].z<64)!=(out[1].z<64):
   uv=(C.c_double*2)();assert near(out[0].z,out[1].z,raw,int(edge['shift']),int(edge['height']),int(edge['affine']),64,recip,uv)
   t=(64-out[0].z)/(out[1].z-out[0].z);intersection=[getattr(out[0],k)+(getattr(out[1],k)-getattr(out[0],k))*t for k in 'xyz']
   assert all(math.isfinite(v) for v in list(uv)+intersection) and abs(intersection[2]-64)<1e-9;clipped+=1
 lo,hi=0.,1.;side=transform(world,poses[i],poses[j],0)[moving].z<64
 for _ in range(45):
  mid=(lo+hi)/2
  if (transform(world,poses[i],poses[j],mid)[moving].z<64)==side:lo=mid
  else:hi=mid
 root=(lo+hi)/2;depth=transform(world,poses[i],poses[j],root)[moving].z;assert abs(depth-64)<1e-9
 roots.append(dict(identity=change['identity'],edge=change['edge'],rigid_interpolation_boundary_fraction=root,boundary_depth=depth))
report=dict(result='PASS',captured_edge_endpoint_reconstructions=len(edges),maximum_camera_coordinate_error=maximum,rigid_edge_samples=samples,clipped_samples=clipped,boundaries=roots,scope='Actual rigid helper reconstructs retained live world edges from logged presented camera poses; dense interpolation between adjacent presented poses, finite clipped geometry/UV and identified near-plane roots. Logged poses rounded; interpolation crosses an original scene-pair knot and is not a recovered full original timeline replay. No GPU pixel/original raster/smooth gameplay proof.')
(p/'live-edge-rigid-replay-tests.json').write_text(json.dumps(report,indent=2));print(report)
