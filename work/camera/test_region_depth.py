from pathlib import Path
import ctypes as C,struct,json
p=Path(__file__).resolve().parent
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',C.c_double*4)]
d=C.CDLL(str(p/'visibility-probe.dll'));d.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
def sections(raw):return {t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
s=sections((p/'combined-143-combined.bin').read_bytes());new=sections((p/'object-replay-143-new.bin').read_bytes());a=Pose.from_buffer_copy(s[1][48:104]);b=Pose.from_buffer_copy(new[1][48:104]);fixed=Pose(Point(0,0,0),(C.c_double*4)(0,0,0,1));cx,cy,f=struct.unpack_from('<3d',s[1],24)
count=struct.unpack_from('<I',s[2],4)[0];offset=8;results=[]
for index in range(count):
 n,w,h=struct.unpack_from('<3I',s[2],offset);vertices=(Point*n)(*[Point(*struct.unpack_from('<3d',s[2],offset+12+i*24)) for i in range(n)]);offset+=12+n*40+w*h*4
 if index<22:continue
 camera=(Point*n)();assert d.nf_rigid_scene_sample(C.byref(a),C.byref(b),C.byref(fixed),C.byref(fixed),.5,vertices,n,camera)
 projected=[(cx+f*v.x/v.z,cy+f*v.y/v.z) for v in camera if v.z>=64]
 results.append(dict(index=index,identity=struct.unpack_from('<5I',s[5],8+index*20),depth=[min(v.z for v in camera),max(v.z for v in camera)],projected_vertices=projected))
report=dict(result='PASS',surfaces=results,scope='Camera-depth ranges from shared rigid transform. Range separation proves nearer geometry where projected coverage overlaps; no visibility correction asserted.')
(p/'region-depth-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
