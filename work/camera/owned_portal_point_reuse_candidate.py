"""Owned raw descriptor graph traversal; no captured projected bounds or call order."""
import struct,math
from functools import lru_cache
from owned_portal_continuous import edge as fixed_continuous_edge
from owned_portal_transform import transform,project_edge
from owned_partition_bounds import record
@lru_cache(maxsize=4096)
def endpoint_delta(x,z,raw,normal):
 fixed=transform(x,z,raw)
 ideal=((x+normal[9])*normal[0]+(z+normal[11])*normal[6],(x+normal[9])*normal[2]+(z+normal[11])*normal[8])
 return fixed[0]-ideal[0],fixed[1]-ideal[1]

def continuous_edge(a,b,near,scale,center,flip):
 x,z=a;nx,nz=b
 if z<near and nz<near:return None
 flags=0
 if z<near:x+=(nx-x)*(near-z)/(nz-z);z=near;flags|=8
 elif nz<near:nx+=(x-nx)*(near-nz)/(z-nz);nz=near;flags|=16
 left,right=center+scale*x/z,center+scale*nx/nz
 if flip and left>right:left,right=right,left
 return left,right,flags,z,nz

def traverse(graph,matrix,framebuffer,root,reciprocal,capacity=256,sampled_camera=None,endpoint_correction=None,diagnostic_trace=None,descriptor_links=None,linked_viewport=None):
 if sampled_camera is not None and (len(sampled_camera)!=12 or not all(math.isfinite(x) for x in sampled_camera)):raise ValueError('Invalid sampled portal camera')
 queue=[tuple(root[:7])];index=0;linked=False
 near=struct.unpack_from('<i',framebuffer,16)[0];scale=struct.unpack_from('<I',framebuffer,28)[0];center=struct.unpack_from('<h',framebuffer,8)[0]
 def uncached_camera_point(point):
  x,z=struct.unpack_from('<2i',point)
  if sampled_camera is None:return transform(x,z,matrix)
  def continuous(m):return (x+m[9])*m[0]+(z+m[11])*m[6],(x+m[9])*m[2]+(z+m[11])*m[8]
  result=continuous(sampled_camera)
  if endpoint_correction is None:return result
  raw_a,raw_b,normal_a,normal_b,alpha=endpoint_correction
  delta_a,delta_b=endpoint_delta(x,z,raw_a,normal_a),endpoint_delta(x,z,raw_b,normal_b)
  return tuple(result[k]+(1-alpha)*delta_a[k]+alpha*delta_b[k] for k in range(2))
 point_cache={}
 def camera_point(point):
  key=point[:8]
  if key not in point_cache:point_cache[key]=uncached_camera_point(point)
  return point_cache[key]
 while index<len(queue):
  # Original builder 03004C74: stop expansion after a region pushes
  # total beyond 20; retain already emitted frontier records.
  if len(queue)>20:break
  parent=queue[index]
  # Original parent +12 <=4 guard; depth-five records remain drawable.
  if parent[0] not in graph:raise ValueError('Missing raw portal descriptor')
  points,top,bottom=graph[parent[0]];n=len(points)//68
  if not n or len(points)%68:raise ValueError('Invalid raw portal ring')
  for i in range(n if parent[6]<=4 else 0):
   point=points[i*68:(i+1)*68];descriptor=struct.unpack_from('<H',point,48)[0]
   if descriptor==65535:continue
   j=(i+1)%n;nextpoint=points[j*68:(j+1)*68]
   a=camera_point(point);b=camera_point(nextpoint)
   if max(a[1],b[1])>0x6000:break
   edge=project_edge(a,b,near,scale,center,reciprocal,index==0) if sampled_camera is None else fixed_continuous_edge(a,b,near,scale,center,reciprocal,index==0)
   if edge is None:continue
   left,right,flags,z,nz=edge
   if left>=right or right<parent[1] or left>=parent[2]:continue
   if diagnostic_trace is not None:diagnostic_trace.append(dict(parent_index=index,parent=parent,edge_index=i,descriptor=descriptor,left=left,right=right,flags=flags,z=z,nz=nz,queue_length=len(queue)))
   if len(queue)>=capacity:raise ValueError('Portal queue capacity exceeded')
   point_flags=struct.unpack_from('<H',point,46)[0]
   if sampled_camera is None:queue.append(record(descriptor,left,right,flags,parent,top,bottom,point_flags,z,nz))
   else:
    lo=2.0 if flags&8 else max(left,parent[1]);hi=238.0 if flags&16 else min(right,parent[2]);bits=parent[5]&128
    if point_flags&0x800:bits=128
    if min(z,nz)>0x800:bits|=1
    queue.append((descriptor,lo,hi,top,bottom,bits,parent[6]+1))
  target=65535 if descriptor_links is None else descriptor_links.get(parent[0],65535)
  if not linked and target!=65535:
   if linked_viewport is None or len(linked_viewport)!=2:raise ValueError('Missing linked viewport')
   if len(queue)>=capacity:raise ValueError('Portal queue capacity exceeded')
   if target not in graph:raise ValueError('Missing linked raw descriptor')
   queue.append((target,*linked_viewport,parent[3],parent[4],128,parent[6],parent[0]))
   linked=True
  index+=1
 return queue
