from pathlib import Path
import ctypes as C,json,math,random,struct
from analyze_world import records
root=Path('work/camera')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quaternion(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quaternion)]
d=C.CDLL(str((root/'rigid_motion.dll').resolve()))
d.nf_pose_decode.argtypes=[C.POINTER(C.c_int32),C.POINTER(Point),C.POINTER(Pose)]
d.nf_pose_sample.argtypes=[C.POINTER(Pose),C.POINTER(Pose),C.c_double,C.POINTER(Pose)]
d.nf_rigid_scene_sample.argtypes=[C.POINTER(Pose)]*4+[C.c_double,C.POINTER(Point),C.c_uint,C.POINTER(Point)]
def decode(matrix,position):
    m=(C.c_int32*12)(*matrix);p=Point(*position);out=Pose()
    assert d.nf_pose_decode(m,C.byref(p),C.byref(out))
    return out
def sample(ca,cb,oa,ob,alpha,points):
    result=(Point*len(points))()
    assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(oa),C.byref(ob),alpha,points,len(points),result)
    return result
def distance(a,b):return math.sqrt((a.x-b.x)**2+(a.y-b.y)**2+(a.z-b.z)**2)
identity=Pose(Point(0,0,0),Quaternion(0,0,0,1))
# A shortest-path rotation from +179 to -179 degrees passes through 180.
def yaw(a):return Pose(Point(0,0,0),Quaternion(0,math.sin(a/2),0,math.cos(a/2)))
a=yaw(math.radians(179));b=yaw(math.radians(-179))
p=(Point*2)(Point(1,0,0),Point(0,0,0))
out=sample(identity,identity,a,b,0.5,p)
assert abs(out[0].x+1)<1e-12 and abs(out[0].z)<1e-12
# q and -q describe the same rotation, including exactly opposite signs.
opposite=Pose(a.position,Quaternion(*[-getattr(a.rotation,k) for k in ('x','y','z','w')]))
for alpha in (0,.25,.5,.75,1):
    original=sample(identity,identity,a,a,0,p)
    got=sample(identity,identity,a,opposite,alpha,p)
    assert distance(original[0],got[0])<1e-12
# Invalid matrices and phases must not overwrite pose output.
invalid=(C.c_int32*12)();saved=bytes(identity);position=Point()
assert not d.nf_pose_decode(invalid,C.byref(position),C.byref(identity)) and bytes(identity)==saved
assert not d.nf_pose_sample(C.byref(a),C.byref(b),float('nan'),C.byref(identity)) and bytes(identity)==saved
reflection=(C.c_int32*12)(-16384,0,0,0,16384,0,0,0,16384,0,0,0)
assert not d.nf_pose_decode(reflection,C.byref(position),C.byref(identity)) and bytes(identity)==saved
# Camera position subtracts before its rotation; object translation adds first.
camera=Pose(Point(10,20,30),Quaternion(0,0,0,1));obj=Pose(Point(11,22,33),Quaternion(0,0,0,1))
result=sample(camera,camera,obj,obj,.5,p)
assert (result[0].x,result[0].y,result[0].z)==(2,2,3)
r=random.Random(6014);max_error=0
decode_error=0
for case in range(1000):
    q=[r.uniform(-1,1) for _ in range(4)];n=math.sqrt(sum(v*v for v in q));x,y,z,w=[v/n for v in q]
    # Independently formed column-major rotation, including all conversion branches.
    matrix=[1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),
            2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),
            2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]
    decoded=decode([round(v*16384) for v in matrix]+[0,0,0],(0,0,0))
    got=sample(identity,identity,decoded,decoded,0,p)[0]
    decode_error=max(decode_error,math.sqrt((got.x-matrix[0])**2+(got.y-matrix[1])**2+(got.z-matrix[2])**2))
assert decode_error<0.0001,decode_error
for case in range(1000):
    poses=[]
    for _ in range(4):
        q=[r.uniform(-1,1) for _ in range(4)];length=math.sqrt(sum(v*v for v in q))
        poses.append(Pose(Point(*[r.uniform(-10000,10000) for _ in range(3)]),Quaternion(*[v/length for v in q])))
    points=(Point*8)(*[Point(*[r.uniform(-500,500) for _ in range(3)]) for _ in range(8)])
    result=sample(*poses,r.random(),points)
    for i in range(1,8):max_error=max(max_error,abs(distance(points[0],points[i])-distance(result[0],result[i])))
assert max_error<1e-8,max_error
# Decode captured independent object orientation, shared camera and world pose.
left_by_slot={};caller=None;snapshots=[]
for e in records(root/'world.bin'):
    b=e['blocks']
    if e['pc']==0x0806db14:left_by_slot[b[73][0]]=b[71][1]
    elif e['pc']==0x03002628:caller=e
    elif e['pc']==0x030045e0 and b[53][0] in left_by_slot:
        cb=caller['blocks'];cam=struct.unpack('<12i',cb[63][1]);rot=struct.unpack('<12i',left_by_slot[b[53][0]])
        world=struct.unpack_from('<3i',cb[62][1],12)
        camera=decode(cam,[-v for v in cam[9:12]])
        obj=decode(rot,[v/256 for v in world])
        values=struct.unpack('<'+'h'*(len(b[54][1])//2),b[54][1])
        points=(Point*(len(values)//3))(*[Point(*values[i:i+3]) for i in range(0,len(values),3)])
        snapshots.append((e['frame'],cb[62][0],b[52][0],camera,obj,points))
checks=0;live_error=0;phase_steps=0;moving_steps=0
for a,b in zip(snapshots,snapshots[1:]):
    if a[1:3]!=b[1:3]:continue
    span=b[0]-a[0]
    assert span>0
    points=a[5];previous=None
    # One shared phase, based on actual capture timestamps, for every vertex.
    for step in range(span+1):
        result=sample(a[3],b[3],a[4],b[4],step/span,points)
        for i in range(1,len(points)):
            live_error=max(live_error,abs(distance(points[0],points[i])-distance(result[0],result[i])))
            checks+=1
        if previous is not None:
            phase_steps+=1
            moving_steps+=any(distance(previous[i],result[i])>1e-9 for i in range(len(points)))
        previous=result
assert checks and live_error<1e-8
report={'result':'PASS','random_rigid_scene_cases':1000,'maximum_random_length_error_world_units':max_error,
 'rotation_decode_cases':1000,'maximum_unit_vector_decode_error':decode_error,
 'captured_pose_samples':len(snapshots),'live_vertex_distance_checks':checks,'maximum_live_length_error_world_units':live_error,
 'presentation_intervals':phase_steps,'intervals_with_changed_model_vertices':moving_steps,
 'scope':'CPU rigid-pose interpolation only, tested on captured geometry. No GPU presentation, full-scene integration, or playable 60-fps claim.'}
(root/'rigid-motion-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
