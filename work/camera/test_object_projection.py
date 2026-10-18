from pathlib import Path
import ctypes as C,struct,json
p=Path(__file__).resolve().parent
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',C.c_double*4)]
d=C.CDLL(str(p/'visibility-probe.dll'))
d.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
fixed=Pose(Point(0,0,0),(C.c_double*4)(0,0,0,1))
def section(raw,tag):
 for i in range(5):
  t,o,n=struct.unpack_from('<3I',raw,32+i*12)
  if t==tag:return raw[o:o+n]
results=[]
for scene in (122,143):
 surface=(p/f'object-candidate-{scene}.bin').read_bytes();n,w,h=struct.unpack_from('<3I',surface)
 vertices=(Point*n)(*[Point(*struct.unpack_from('<3d',surface,12+i*24)) for i in range(n)])
 models=[section((p/f'object-replay-{scene}-{label}.bin').read_bytes(),1) for label in ('old','new')]
 poses=[Pose.from_buffer_copy(model[48:104]) for model in models]
 camera=(Point*n)();assert d.nf_rigid_scene_sample(C.byref(poses[0]),C.byref(poses[1]),C.byref(fixed),C.byref(fixed),.5,vertices,n,camera)
 polygon=[(v.x,v.y,v.z) for v in camera];clipped=[]
 for a,b in zip(polygon,polygon[1:]+polygon[:1]):
  if a[2]>=64:clipped.append(a)
  if (a[2]>=64)!=(b[2]>=64):
   t=(64-a[2])/(b[2]-a[2]);clipped.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
 cx,cy,f=struct.unpack_from('<3d',models[0],24)
 screen=[(cx+f*x/z,cy+f*y/z) for x,y,z in clipped]
 bbox=[min(v[0] for v in screen),min(v[1] for v in screen),max(v[0] for v in screen),max(v[1] for v in screen)] if screen else None
 alpha=surface[12+n*40+3::4]
 results.append(dict(scene=scene,camera=polygon,projected=screen,bbox=bbox,opaque_texels=sum(a!=0 for a in alpha),texture_texels=w*h))
report=dict(result='PASS',cases=results,scope='Shared native pose transform and near-plane64 projection diagnostics; no occlusion or full-scene proof.')
(p/'object-projection-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

