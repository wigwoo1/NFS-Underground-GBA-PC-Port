"""Project recovered entrant geometry with shared native camera sampling."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'native_surface.dll').resolve()))
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
d.nf_rigid_scene_sample.argtypes=[C.POINTER(Pose)]*4+[C.c_double,C.POINTER(Point),C.c_uint,C.POINTER(Point)]
def packet(serial):
 b=(p/f'order-boundary-{serial}.bin').read_bytes();s={t:b[o:o+n] for t,o,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]};return s
old=packet(140);new=packet(141);world=new[2];pos=8;vertices=None
for i in range(struct.unpack_from('<I',world,4)[0]):
 n,w,h=struct.unpack_from('<3I',world,pos)
 if struct.unpack_from('<5I',new[5],8+i*20)==(2,50331840,139937176,37,0):vertices=(Point*n).from_buffer_copy(world[pos+12:pos+12+n*24])
 pos+=12+n*40+w*h*4
assert vertices is not None
ca=Pose.from_buffer_copy(old[1][48:104]);cb=Pose.from_buffer_copy(new[1][48:104]);fixed=Pose(Point(0,0,0),Quat(0,0,0,1));projection=struct.unpack_from('<3d',new[1],24)
def clipped(points):
 out=[]
 for i,b in enumerate(points):
  a=points[i-1];ai=a[2]>=64;bi=b[2]>=64
  if ai!=bi:
   t=(64-a[2])/(b[2]-a[2]);out.append([a[j]+(b[j]-a[j])*t for j in range(3)])
  if bi:out.append(b)
 return out
samples=[]
for alpha in [0,.25,.5,.75,1]:
 out=(Point*len(vertices))();assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(fixed),C.byref(fixed),alpha,vertices,len(vertices),out)
 xyz=[[v.x,v.y,v.z] for v in out];clip=clipped(xyz);xy=[[projection[0]+projection[2]*x/z,projection[1]+projection[2]*y/z] for x,y,z in clip]
 bounds=[min(v[0] for v in xy),min(v[1] for v in xy),max(v[0] for v in xy),max(v[1] for v in xy)] if xy else None
 samples.append(dict(alpha=alpha,depth_range=[min(v.z for v in out),max(v.z for v in out)],screen_bounds=bounds,viewport_bounds_overlap=bool(bounds and bounds[0]<240 and bounds[2]>0 and bounds[1]<160 and bounds[3]>0)))
lo,hi=0.,1.
for _ in range(40):
 mid=(lo+hi)/2;out=(Point*len(vertices))();assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(fixed),C.byref(fixed),mid,vertices,len(vertices),out)
 right=max(projection[0]+projection[2]*v.x/v.z for v in out)
 if right>0:hi=mid
 else:lo=mid
report=dict(first_horizontal_overlap_alpha=hi,samples=samples,scope='Recovered identity world vertices projected through native shared pose sampler. Bounding overlap is only a conservative frustum candidate test, not occlusion or source visibility proof.')
(p/'entrant-projection-tests.json').write_text(json.dumps(report,indent=2));print(report)

