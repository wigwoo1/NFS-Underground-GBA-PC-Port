"""Rigid road camera sampling with original fixed-point endpoint corrections."""
import math
from owned_road_rigid_candidate import rigid_points
from functools import lru_cache

def _signed(value,bits):
 value&=(1<<bits)-1
 return value-(1<<bits) if value&(1<<(bits-1)) else value

def _fixed(point,matrix):
 x,y,z=point
 if int(x)!=x or int(z)!=z:raise ValueError('Fractional raw road world source unsupported')
 def axis(k):return _signed(_signed((int(x)+matrix[9])*matrix[k]+(int(z)+matrix[11])*matrix[6+k],32)>>14,16)
 return (axis(0),y+matrix[10],axis(2))
def _rigid(point,pose):
 x=point[0]+pose[9];y=point[1]+pose[10];z=point[2]+pose[11]
 # Keep Python sum's compensated float arithmetic; remove generators only.
 return (sum((x*pose[0],y*pose[3],z*pose[6])),sum((x*pose[1],y*pose[4],z*pose[7])),sum((x*pose[2],y*pose[5],z*pose[8])))
@lru_cache(maxsize=64)
def _world_endpoint_projections(world,old_matrix,new_matrix,endpoint_poses):
 result=[]
 for i in range(0,len(world),3):
  point=world[i:i+3]
  result.append((_fixed(point,old_matrix),_fixed(point,new_matrix),_rigid(point,endpoint_poses[0]),_rigid(point,endpoint_poses[1])))
 return tuple(result)

def sampled_road_camera(world,old_matrix,new_matrix,endpoint_poses,camera,alpha):
 if not math.isfinite(alpha) or not 0<=alpha<=1 or len(world)%3:raise ValueError('Invalid road camera sample')
 if len(old_matrix)!=12 or len(new_matrix)!=12 or len(camera)!=12 or len(endpoint_poses)!=2 or any(len(p)!=12 for p in endpoint_poses):raise ValueError('Incomplete road camera matrices')
 if not all(math.isfinite(x) for x in (*world,*camera,*endpoint_poses[0],*endpoint_poses[1])):raise ValueError('Nonfinite road camera source')
 out=[]
 endpoint_values=_world_endpoint_projections(tuple(world),tuple(old_matrix),tuple(new_matrix),tuple(tuple(p) for p in endpoint_poses)) if 0<alpha<1 else None
 batch=rigid_points(tuple(world),tuple(camera)) if 0<alpha<1 and 0<len(world)<=96 else None
 for i in range(0,len(world),3):
  point=tuple(world[i:i+3])
  if endpoint_values is None:
   a,b=_fixed(point,old_matrix),_fixed(point,new_matrix)
   out.extend(a if alpha==0 else b);continue
  a,b,pa,pb=endpoint_values[i//3];p=batch[i:i+3] if batch is not None else _rigid(point,camera)
  value=tuple(p[k]+(a[k]-pa[k])*(1-alpha)+(b[k]-pb[k])*alpha for k in range(3))
  if any(abs(value[k])>32767 for k in (0,2)):raise ValueError('Sampled signed road camera wrap unsupported')
  out.extend(value)
 return tuple(out)


def _rigid_depth(point,pose):
 x=point[0]+pose[9];y=point[1]+pose[10];z=point[2]+pose[11]
 return sum((x*pose[2],y*pose[5],z*pose[8]))

@lru_cache(maxsize=64)
def _far_endpoint_projections(world,old_matrix,new_matrix,endpoint_poses):
 out=[]
 for i in range(0,len(world),3):
  point=tuple(world[i:i+3]);x,y,z=point
  if not all(math.isfinite(v) for v in point):raise ValueError('Nonfinite far source')
  if int(x)!=x or int(z)!=z:raise ValueError('Fractional raw far source unsupported')
  def endpoint(m):return _signed((int(x)+m[9])*m[2]+(int(z)+m[11])*m[8],32)>>14
  out.append((endpoint(old_matrix),endpoint(new_matrix),_rigid_depth(point,endpoint_poses[0]),_rigid_depth(point,endpoint_poses[1])))
 return tuple(out)

def sampled_road_far_depths(world,old_matrix,new_matrix,endpoint_poses,camera,alpha):
 """Far gate uses original signed32/Q14 result before signed16 wrapping."""
 if not math.isfinite(alpha) or not 0<=alpha<=1 or len(world)%3:raise ValueError('Invalid road far sample')
 if any(len(p)!=12 for p in (old_matrix,new_matrix,camera,*endpoint_poses)) or len(endpoint_poses)!=2:raise ValueError('Incomplete far matrices')
 out=[]
 endpoint_values=_far_endpoint_projections(tuple(world),tuple(old_matrix),tuple(new_matrix),tuple(tuple(p) for p in endpoint_poses))
 batch=rigid_points(tuple(world),tuple(camera)) if 0<alpha<1 and 0<len(world)<=96 else None
 for i in range(0,len(world),3):
  point=tuple(world[i:i+3]);a,b,pa,pb=endpoint_values[i//3]
  if alpha==0:out.append(a);continue
  if alpha==1:out.append(b);continue
  value=(batch[i+2] if batch is not None else _rigid_depth(point,camera))+(a-pa)*(1-alpha)+(b-pb)*alpha
  if not math.isfinite(value):raise ValueError('Nonfinite far correction')
  # A signed16 wrap crossing needs independently recovered near-depth handling.
  if (a<-32768 or a>32767)!=(b<-32768 or b>32767):
   if not (a>0x5fff and b>0x5fff and value>0x5fff):raise ValueError('Far/near wrap transition unsupported')
  out.append(value)
 return tuple(out)
