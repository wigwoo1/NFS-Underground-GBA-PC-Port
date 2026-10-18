"""Owned raw world/camera pose sampling for diagnostic GPU intermediates."""
import ctypes as C,struct,math
from pathlib import Path
from collections import OrderedDict
_rigid_library_path=str(Path(__file__).with_name('rigid-motion-source-tests.dll').resolve())
from owned_motion_pairs import plan_pair
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
def _sample_prepared(older,newer,alpha,plan,d,ca,cb,objects,basis):
 if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid motion alpha')
 if alpha==0:return older,None,None
 if alpha==1:return newer,None,None
 cs=Pose();assert d.nf_pose_sample(C.byref(ca),C.byref(cb),alpha,C.byref(cs));x,y,z,w=cs.rotation.x,cs.rotation.y,cs.rotation.z,cs.rotation.w
 rows=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
 camera=(C.c_double*12)(*[rows[r][c] for c in range(3) for r in range(3)],-cs.position.x,-cs.position.y,-cs.position.z)
 models=(C.c_double*(12*len(plan['older']['records'])))()
 for i,oa,ob in objects:
  out=(Point*4)();assert d.nf_rigid_scene_sample(C.byref(ca),C.byref(cb),C.byref(oa),C.byref(ob),alpha,basis,4,out)
  for k,name in enumerate(('x','y','z')):
   models[i*12+9+k]=getattr(out[0],name)
   for col in range(3):models[i*12+col*3+k]=getattr(out[col+1],name)-getattr(out[0],name)
 return older,camera,models

from functools import lru_cache
@lru_cache(maxsize=1)
def rigid_library():
 d=C.CDLL(_rigid_library_path)
 d.nf_model_world_pose.argtypes=[C.c_void_p]*4;d.nf_pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p];d.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
 return d

class PreparedMotionPair:
 """Own two immutable frames; validate identities and decode endpoint poses once."""
 def __init__(self,older,newer,older_scene=None,newer_scene=None):
  self.older=bytes(older);self.newer=bytes(newer);plan=plan_pair(self.older,self.newer)
  if (older_scene is None)!=(newer_scene is None):raise ValueError('Incomplete motion scene pair')
  self.scene_pair=None if older_scene is None else (older_scene.match(self.older),newer_scene.match(self.newer))
  d=rigid_library()
  cm_a=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));cm_b=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']))
  identity=(C.c_int32*12)(16384,0,0,0,16384,0,0,0,16384,0,0,0);ca=Pose();cb=Pose();unused=Pose()
  assert d.nf_model_world_pose(cm_a,identity,C.byref(ca),C.byref(unused));assert d.nf_model_world_pose(cm_b,identity,C.byref(cb),C.byref(unused))
  objects=[];pairmap=dict(plan['pairs']);basis=(Point*4)(Point(0,0,0),Point(1,0,0),Point(0,1,0),Point(0,0,1))
  for i,record in enumerate(plan['older']['records']):
   if record['kind']!=3:continue
   ma=(C.c_int32*12)(*struct.unpack('<12i',record['blocks'][2]));oa=Pose();ob=Pose();assert d.nf_model_world_pose(cm_a,ma,C.byref(unused),C.byref(oa))
   if i in pairmap:
    newer_record=plan['newer']['records'][pairmap[i]];mb=(C.c_int32*12)(*struct.unpack('<12i',newer_record['blocks'][2]));assert d.nf_model_world_pose(cm_b,mb,C.byref(unused),C.byref(ob))
   else:ob=oa
   objects.append((i,oa,ob))
  self.arguments=(plan,d,ca,cb,objects,basis);self._sample_cache=OrderedDict()
 def sample(self,alpha):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid motion alpha')
  if alpha in (0,1):return _sample_prepared(self.older,self.newer,alpha,*self.arguments)
  if alpha not in self._sample_cache:
   _,camera,models=_sample_prepared(self.older,self.newer,alpha,*self.arguments)
   # Retain values only. Every caller gets private mutable ctypes storage.
   self._sample_cache[alpha]=(tuple(camera),bytes(models))
  self._sample_cache.move_to_end(alpha)
  while len(self._sample_cache)>8:self._sample_cache.popitem(last=False)
  camera,models=self._sample_cache[alpha]
  return self.older,(C.c_double*12)(*camera),(C.c_double*(len(models)//8)).from_buffer_copy(models)

def sample(older,newer,alpha):return PreparedMotionPair(older,newer).sample(alpha)
