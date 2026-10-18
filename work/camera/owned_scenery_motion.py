"""Rigid motion from complete source-owned scenery candidate record pairs."""
import ctypes as C,struct,math
from pathlib import Path
_rigid_library_path=str(Path(__file__).with_name('rigid-motion-source-tests.dll').resolve())
from types import MappingProxyType
from sample_owned_motion import Point,Pose

def normalized_matrix(raw):
 values=struct.unpack('<12i',raw)
 return tuple(value/16384 if i<9 else float(value) for i,value in enumerate(values))

class PreparedSceneryMotion:
 def __init__(self,pairs,camera_older,camera_newer):
  self._lib=C.CDLL(_rigid_library_path)
  self._lib.nf_model_world_pose.argtypes=[C.c_void_p]*4
  self._lib.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
  self._basis=(Point*4)(Point(0,0,0),Point(1,0,0),Point(0,1,0),Point(0,0,1))
  self._camera_raw=tuple(bytes(raw) for raw in (camera_older,camera_newer))
  if any(len(raw)!=48 for raw in self._camera_raw):raise ValueError('Incomplete scenery camera ownership')
  prepared={}
  for pair in pairs:
   if pair.object_index in prepared:raise ValueError('Repeated scenery motion source')
   cameras=[];objects=[]
   for raw,blocks in zip(self._camera_raw,(pair.older_blocks,pair.newer_blocks)):
    camera=Pose();obj=Pose();cm=(C.c_int32*12)(*struct.unpack('<12i',raw));mm=(C.c_int32*12)(*struct.unpack('<12i',blocks[2]))
    if not self._lib.nf_model_world_pose(cm,mm,C.byref(camera),C.byref(obj)):raise ValueError('Unsupported scenery rigid pose')
    cameras.append(camera);objects.append(obj)
   endpoints=tuple(self._rigid(cameras,objects,t) for t in (0,1))
   exact=tuple(normalized_matrix(blocks[2]) for blocks in (pair.older_blocks,pair.newer_blocks))
   corrections=tuple(tuple(a-b for a,b in zip(wanted,rigid)) for wanted,rigid in zip(exact,endpoints))
   prepared[pair.object_index]=(pair,tuple(cameras),tuple(objects),corrections)
  self._prepared=MappingProxyType(prepared)
 def matrix(self,object_index,alpha):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid scenery motion alpha')
  if object_index not in self._prepared:raise ValueError('Missing scenery motion source')
  pair,cameras,objects,corrections=self._prepared[object_index]
  if alpha in (0,1):return normalized_matrix((pair.older_blocks,pair.newer_blocks)[int(alpha)][2])
  rigid=self._rigid(cameras,objects,alpha)
  result=tuple(value+(1-alpha)*corrections[0][i]+alpha*corrections[1][i] for i,value in enumerate(rigid))
  if not all(math.isfinite(v) for v in result):raise ValueError('Invalid scenery motion matrix')
  return result
 def _rigid(self,cameras,objects,alpha):
  out=(Point*4)()
  if not self._lib.nf_rigid_scene_sample(C.byref(cameras[0]),C.byref(cameras[1]),C.byref(objects[0]),C.byref(objects[1]),alpha,self._basis,4,out):raise ValueError('Scenery motion sample failed')
  return tuple(getattr(out[col+1],name)-getattr(out[0],name) for col in range(3) for name in ('x','y','z'))+tuple(getattr(out[0],name) for name in ('x','y','z'))
