"""Conservative projected bounds for owned, enumerated world candidates."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'native_surface.dll').resolve()))
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
d.nf_rigid_scene_sample.argtypes=[C.POINTER(Pose)]*4+[C.c_double,C.POINTER(Point),C.c_uint,C.POINTER(Point)]
def model(serial):
 b=(p/f'order-boundary-{serial}.bin').read_bytes();tag,off,size=struct.unpack_from('<3I',b,32);assert tag==1;return b[off:off+size]
a=model(140);b=model(141);ca=Pose.from_buffer_copy(a[48:104]);cb=Pose.from_buffer_copy(b[48:104]);fixed=Pose(Point(0,0,0),Quat(0,0,0,1));cx,cy,focal=struct.unpack_from('<3d',a,24)
def clip(points):
 result=[]
 for i,b in enumerate(points):
  a=points[i-1];ai=a[2]>=64;bi=b[2]>=64
  if ai!=bi:
   t=(64-a[2])/(b[2]-a[2]);result.append([a[j]+t*(b[j]-a[j]) for j in range(3)])
  if bi:result.append(b)
 return result
sources=json.loads((p/'texture-provenance-tests.json').read_text())['enumeration'][0]['accepted'];results=[]
for item in sources:
 data=(p/f"enumerated-140-{item['source']}.bin").read_bytes();n=struct.unpack_from('<I',data)[0];vertices=(Point*n).from_buffer_copy(data[12:12+n*24]);samples=[]
 for alpha in (0,.25,.5,.75,1):
  out=(Point*n)();assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(fixed),C.byref(fixed),alpha,vertices,n,out)
  points=clip([[v.x,v.y,v.z] for v in out]);xy=[(cx+focal*x/z,cy+focal*y/z) for x,y,z in points]
  bounds=[min(x for x,y in xy),min(y for x,y in xy),max(x for x,y in xy),max(y for x,y in xy)] if xy else None
  area=sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1] for i in range(len(xy))) if xy else 0
  overlap=bool(bounds and bounds[0]<240 and bounds[2]>0 and bounds[1]<160 and bounds[3]>0)
  samples.append(dict(alpha=alpha,bounds=bounds,signed_area=area,overlap=overlap))
 results.append(dict(source=item['source'],samples=samples))
visible=[r['source'] for r in results if any(s['overlap'] for s in r['samples'])]
report=dict(result='PASS',candidates=len(results),sampled_overlap_sources=visible,results=results,scope='Five sampled camera poses, near-clipped projected bounding boxes; does not prove continuous interval exclusion, backface convention or portal visibility.')
(p/'candidate-frustum-tests.json').write_text(json.dumps(report,indent=2));print(dict(candidates=len(results),sampled_overlap_sources=visible))
