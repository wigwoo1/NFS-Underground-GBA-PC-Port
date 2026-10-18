from pathlib import Path
import json,struct,hashlib,ctypes as C
p=Path(__file__).resolve().parent
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',C.c_double*4)]
d=C.CDLL(str(p/'visibility-probe.dll'));d.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
def sections(raw):return {t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
packets=[sections((p/f'object-replay-143-{v}.bin').read_bytes()) for v in ('old','new')]
assets=[]
for s in packets:
 offset=8;found=[]
 for index in range(struct.unpack_from('<I',s[2],4)[0]):
  n,w,h=struct.unpack_from('<3I',s[2],offset);size=12+40*n+w*h*4;ident=struct.unpack_from('<5I',s[5],8+index*20)
  if ident[2]==139970292:found.append((ident,s[2][offset:offset+size]))
  offset+=size
 assert len(found)==1;assets.append(found[0])
assert assets[0][0]==assets[1][0]
na=struct.unpack_from('<I',assets[0][1])[0];nb=struct.unpack_from('<I',assets[1][1])[0]
assert na==nb and assets[0][1][:12+na*40]==assets[1][1][:12+nb*40]
alpha_equal=assets[0][1][12+na*40+3::4]==assets[1][1][12+nb*40+3::4]
surface=assets[0][1];n,w,h=struct.unpack_from('<3I',surface);vertices=(Point*n)(*[Point(*struct.unpack_from('<3d',surface,12+i*24)) for i in range(n)])
a,b=[Pose.from_buffer_copy(s[1][48:104]) for s in packets];fixed=Pose(Point(0,0,0),(C.c_double*4)(0,0,0,1));cx,cy,f=struct.unpack_from('<3d',packets[0][1],24);phases=[]
for alpha in (0,.25,.5,.75,1):
 camera=(Point*n)();assert d.nf_rigid_scene_sample(C.byref(a),C.byref(b),C.byref(fixed),C.byref(fixed),alpha,vertices,n,camera)
 polygon=[(v.x,v.y,v.z) for v in camera];clipped=[]
 for v,z in zip(polygon,polygon[1:]+polygon[:1]):
  if v[2]>=64:clipped.append(v)
  if (v[2]>=64)!=(z[2]>=64):
   t=(64-v[2])/(z[2]-v[2]);clipped.append(tuple(v[k]+t*(z[k]-v[k]) for k in range(3)))
 projected=[(cx+f*x/z,cy+f*y/z) for x,y,z in clipped]
 phases.append(dict(alpha=alpha,depth=[min(v.z for v in camera),max(v.z for v in camera)],near_clipped_vertices=len(clipped),projected=projected))
trace=json.loads((p/'texture-provenance-tests.json').read_text());origins=[]
for row in trace['dispatch_samples']:
 if row['serial'] not in (143,144):continue
 for command,origin,wallpass in zip(row['commands'],row['origins'],row['wall_passes']):
  if 139970292 in command:origins.append(dict(serial=row['serial'],command=command,origin=origin,wall_pass=wallpass))
assert len(origins)==2 and origins[0]['origin']==origins[1]['origin'] and origins[0]['wall_pass']==origins[1]['wall_pass']
report=dict(result='PASS',identity=assets[0][0],endpoint_surface_identical=assets[0]==assets[1],geometry_uv_identical=True,texture_alpha_identical=alpha_equal,surface_sha256=hashlib.sha256(surface).hexdigest(),phases=phases,captured_origins=origins,scope='Endpoint identity matches; surface changes across143/144. Shared camera interpolation and near64 clipping checked; object invocation state and original sampled eligibility still require validation.')
(p/'occluder-endpoint-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


