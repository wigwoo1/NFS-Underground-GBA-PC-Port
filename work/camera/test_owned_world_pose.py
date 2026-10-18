from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');r=json.loads((p/'owned-motion-source-audit.json').read_text())
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
d=C.CDLL(str((p/'rigid-motion-source-tests.dll').resolve()));d.nf_model_world_pose.argtypes=[C.c_void_p]*4;cases=0;max_error=0
for f in r['frames']:
 cm=(C.c_int32*12)(*f['camera_matrix'])
 for m in f['models']:
  mm=(C.c_int32*12)(*m['model_matrix']);camera=Pose();obj=Pose()
  assert d.nf_model_world_pose(cm,mm,C.byref(camera),C.byref(obj))
  actual=[obj.position.x,obj.position.y,obj.position.z];e=max(abs(a-b) for a,b in zip(actual,m['world_position']));assert e<1e-7;max_error=max(max_error,e)
  for pose in (camera,obj):assert abs(sum(getattr(pose.rotation,k)**2 for k in ('x','y','z','w'))-1)<1e-12
  cases+=1
bad=(C.c_int32*12)();camera=Pose();obj=Pose();C.memset(C.byref(camera),0x55,C.sizeof(camera));C.memset(C.byref(obj),0x66,C.sizeof(obj));before=(bytes(camera),bytes(obj));assert not d.nf_model_world_pose(bad,mm,C.byref(camera),C.byref(obj));assert before==(bytes(camera),bytes(obj))
result=dict(result='PASS_RAW_MODEL_WORLD_POSE',actual_source_cases=cases,max_world_position_error=max_error,unit_quaternions=True,degenerate_camera_rejection_atomic=True,scope='Raw world-pose factorization component only; not integrated interpolation or60fps gameplay.')
(p/'owned-world-pose-tests.json').write_text(json.dumps(result,indent=2));print(result)
