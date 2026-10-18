"""Owned portal visibility at a sampled rigid camera; discrete endpoints exact."""
import math,struct
from owned_wall_region_candidates import regions,merge_regions
from owned_portal_traversal import traverse

def normalized(raw):return tuple(x/16384 if i<9 else float(x) for i,x in enumerate(raw))

def sampled_regions(older,newer,reciprocal,camera,alpha,endpoint_cameras=None):
 if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid visibility alpha')
 older.validate();newer.validate()
 if alpha==0:return regions(older,reciprocal)
 if alpha==1:return regions(newer,reciprocal)
 if len(camera)!=12 or not all(math.isfinite(x) for x in camera):raise ValueError('Invalid visibility camera')
 a=older.graph()[0];b=newer.graph()[0]
 if a.keys()!=b.keys() or any(a[k][0]!=b[k][0] for k in a):raise ValueError('Unverified portal topology transition')
 root_a=struct.unpack_from('<8H',older.context,368);root_b=struct.unpack_from('<8H',newer.context,368)
 if root_a[0]!=root_b[0]:raise ValueError('Unverified root region transition')
 ma=struct.unpack_from('<12i',older.context,256);mb=struct.unpack_from('<12i',newer.context,256)
 def projection(context):
  fb=context[304:368];return struct.unpack_from('<i',fb,16)[0],struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0]
 if projection(older.context)!=projection(newer.context):raise ValueError('Unverified projection parameter transition')
 endpoints=(normalized(ma),normalized(mb)) if endpoint_cameras is None else endpoint_cameras
 if len(endpoints)!=2 or any(len(m)!=12 or not all(math.isfinite(x) for x in m) for m in endpoints):raise ValueError('Invalid endpoint camera correction')
 correction=(ma,mb,tuple(endpoints[0]),tuple(endpoints[1]),alpha)
 queue=traverse(a,ma,older.context[304:368],root_a,reciprocal,sampled_camera=tuple(camera),endpoint_correction=correction)
 return merge_regions(queue)

def pose_camera(pose):
 x,y,z,w=pose.rotation.x,pose.rotation.y,pose.rotation.z,pose.rotation.w
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return tuple(rows[r][c] for c in range(3) for r in range(3))+(-pose.position.x,-pose.position.y,-pose.position.z)

class PortalMotionPair:
 """Portal correction uses the same rigid endpoints as camera interpolation."""
 def __init__(self,older,newer,reciprocal,motion_pair):
  self.older=older;self.newer=newer;self.reciprocal=reciprocal;self.motion=motion_pair
  self.endpoints=tuple(pose_camera(p) for p in motion_pair.arguments[2:4])
 def sample(self,alpha):
  if alpha in (0,1):camera=()
  else:_,camera,_=self.motion.sample(alpha)
  return sampled_regions(self.older,self.newer,self.reciprocal,tuple(camera),alpha,self.endpoints)
