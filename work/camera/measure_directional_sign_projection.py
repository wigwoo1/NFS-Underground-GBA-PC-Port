"""Measure native sign projected corners against actual original prepared edge fields."""
import ctypes as C,hashlib,json,struct,sys,math
from pathlib import Path
from scene_batches import batches
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));f=d.nf_rigid_scene_sample;f.argtypes=[C.POINTER(Pose)]*4+[C.c_double,C.POINTER(Point),C.c_uint,C.POINTER(Point)]
path=Path(sys.argv[1]);capture=json.loads(path.read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256'];sources=json.loads(Path(sys.argv[2]).read_text());packets={tuple(r['identity'][2:]):r for r in sources['original_endpoints']};checks=[]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in packets:continue
 row=packets[key];data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))};models=sections[1];offset=struct.unpack_from('<I',models,8)[0] if models[:4]==b'NML1' else 0;model=models[offset:];projection=struct.unpack_from('<3d',model,24);pose=Pose.from_buffer_copy(model[48:104]);fixed=Pose(Point(0,0,0),Quat(0,0,0,1));world=sections[2];count=struct.unpack_from('<I',world,4)[0];position=8
 for i in range(count):
  n,w,h=struct.unpack_from('<3I',world,position);kind,state,source,_,_=struct.unpack_from('<5I',sections[5],8+i*20)
  if kind==2 and source==0x08574c3c:vertices=(Point*4).from_buffer_copy(world[position+12:position+108]);assert n==4
  position+=12+n*40+w*h*4
 points=(Point*4)();assert f(C.byref(pose),C.byref(pose),C.byref(fixed),C.byref(fixed),0,vertices,4,points);assert all(v.z>=64 for v in points)
 projected=[[projection[0]+projection[2]*v.x/v.z,projection[1]+projection[2]*v.y/v.z,v.z] for v in points]
 for e in batch['events']:
  if e['pc']!=0x03000304 or e['blocks'][5][0]!=0x08574c3c:continue
  edge=e['blocks'][6][1];prepared=list(struct.unpack_from('<8h',edge));expected=[math.floor(min(projected[0][0],projected[1][0])),math.floor(max(projected[0][0],projected[1][0])),math.floor(projected[0][2]),math.floor(projected[1][2]),math.floor(projected[0][1]),math.floor(projected[1][1]),math.floor(projected[3][1]),math.floor(projected[2][1])];assert prepared==expected,(key,prepared,expected);native_left=min(projected[0][0],projected[1][0]);native_right=max(projected[0][0],projected[1][0])
  checks.append(dict(interval=key,projection=projection,native_corners=projected,original_prepared_edge_xy_depth=prepared,horizontal_delta=[native_left-prepared[0],native_right-prepared[1]],original_edge_equals_native_integer_floor=True,original_edge_flags=hex(struct.unpack_from('<I',edge,48)[0])))
assert len(checks)==6
out=path.with_name(path.stem.replace('-verification','-sign-projection-measurement')+'.json');out.write_text(json.dumps(dict(result='MEASURED',checks=checks,scope='Actual native rigid transform/projection of owned world corners versus captured original prepared integer wall edges. No inferred screen-polygon matching; measurements do not equate continuous native geometry to quantized original raster.'),indent=2));print(json.dumps(checks))
