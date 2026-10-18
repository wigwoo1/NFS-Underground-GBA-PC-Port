"""Continuous extension of recovered wall visibility arithmetic, independent of raster draw."""
import struct,math
from dataclasses import dataclass
from owned_portal_continuous import cells,blend,coordinate,projection_depth,coordinate_at_depth
from owned_wall_region_candidates import hidden,source_flags
from owned_wall_transform import transform
@dataclass(frozen=True)
class WallVisibility:
 visible:bool
 reason:str
 x:tuple=()
 y:tuple=()
 flags:int=0

def signed16(v):
 v=int(v)&65535
 return v-65536 if v&32768 else v

def wall_near_delta(travel,span,difference,reciprocal):
 # Preserve the wall-specific unsigned factor and original cell blend order.
 t=math.floor(travel);s=math.floor(span);d=math.floor(difference)
 ft=travel-t;fs=span-s;fd=difference-d
 def at_span(ti,si):
  factor=(ti*reciprocal[si])&0xffffffff
  a=(d*factor)>>24
  return a if fd==0 else blend(a,((d+1)*factor)>>24,fd)
 def at_travel(ti):
  a=at_span(ti,s)
  return a if fs==0 else blend(a,at_span(ti,s+1),fs)
 a=at_travel(t)
 return a if ft==0 else blend(a,at_travel(t+1),ft)

def select_wall(wall,descriptor,edge_camera,framebuffer,bounds,base_material,reciprocal):
 # Inputs retain fractional camera-space values; no pose or clip rounding.
 if not all(math.isfinite(x) for x in (*edge_camera,*bounds)):raise ValueError('Nonfinite wall visibility input')
 if hidden(wall):return WallVisibility(False,'hidden')
 if not struct.unpack_from('<H',base_material)[0]:return WallVisibility(False,'inactive_material')
 x,nx,z,nz,*ys=edge_camera
 near=struct.unpack_from('<i',framebuffer,16)[0];scale=struct.unpack_from('<I',framebuffer,28)[0]
 cx,cy=struct.unpack_from('<2h',framebuffer,8);flags=source_flags(wall)
 if z<near and nz<near:return WallVisibility(False,'near_rejected')
 if z<near or nz<near:
  start=z<near;travel=near-(z if start else nz);span=nz-z if start else z-nz
  if span<1 or span>=len(reciprocal)-1:raise ValueError('Unsupported continuous wall near interval')
  def delta(difference):
   # Original wall_scale uses signed64 multiplication of signed32 difference.
   return wall_near_delta(travel,span,difference,reciprocal)
  adjustment=delta(nx-x)
  if start:x+=adjustment;z=near;flags|=8
  else:nx-=adjustment;nz=near;flags|=16
  for a,b in ((0,1),(2,3)):
   adjustment=delta(ys[b]-ys[a])
   if start:ys[a]+=adjustment
   else:ys[b]-=adjustment
 depth=projection_depth(z,scale,reciprocal);next_depth=projection_depth(nz,scale,reciprocal)
 left,right=coordinate_at_depth(x,depth,cx),coordinate_at_depth(nx,next_depth,cx)
 if flags&0x2000 and right<left:flags|=2
 if flags&2:left,right=right,left
 if right<=left or right<bounds[0] or left>=bounds[1]:return WallVisibility(False,'viewport_rejected',(left,right),(),flags|4)
 y=tuple(coordinate_at_depth(v,depth if i%2==0 else next_depth,cy) for i,v in enumerate(ys))
 if y[0]>=bounds[3] and y[1]>=bounds[3] and y[2]<bounds[2] and y[3]<bounds[2]:return WallVisibility(False,'vertical_rejected',(left,right),y,flags)
 return WallVisibility(True,'visible',(left,right),y,flags)

def endpoint_edge(wall,ring,camera,offsets=None):
 offsets=bytes(len(ring)//68*32) if offsets is None else offsets
 ok,raw=transform(ring,offsets,camera)
 if not ok:return None
 scratch=raw[wall.edge*52:(wall.edge+1)*52]
 return (*struct.unpack_from('<4h',scratch),*struct.unpack_from('<4h',scratch,8))

from functools import lru_cache

@lru_cache(maxsize=32)
def _ring_endpoint_corrections(ring,offsets,old_camera,new_camera,endpoints):
 worlds=[]
 for i in range(len(ring)//68):
  x,z=struct.unpack_from('<2i',ring,i*68)
  if struct.unpack_from('<H',ring,i*68+42)[0]!=65535:
   dx,dz=struct.unpack_from('<2h',offsets,i*32);x+=dx;z+=dz
  if not all(-0x80000000<=v<0x80000000 for v in (x,z)):raise ValueError('Unsupported sampled world offset wrap')
  worlds.append((x,z))
 old_fixed=struct.unpack('<12i',old_camera);new_fixed=struct.unpack('<12i',new_camera)
 from owned_portal_transform import transform as fixed_transform
 corrections=[]
 for x,z in worlds:
  fa=fixed_transform(x,z,old_fixed);fb=fixed_transform(x,z,new_fixed)
  a,b=endpoints
  ax=(x+a[9])*a[0]+(z+a[11])*a[6];az=(x+a[9])*a[2]+(z+a[11])*a[8]
  bx=(x+b[9])*b[0]+(z+b[11])*b[6];bz=(x+b[9])*b[2]+(z+b[11])*b[8]
  corrections.append((fa[0]-ax,fa[1]-az,fb[0]-bx,fb[1]-bz))
 return tuple(worlds),tuple(corrections),old_fixed,new_fixed

@lru_cache(maxsize=32)
def _sampled_ring_points(ring,offsets,old_camera,new_camera,camera,endpoints,alpha):
 worlds,corrections,old_fixed,new_fixed=_ring_endpoint_corrections(ring,offsets,old_camera,new_camera,endpoints)
 points=[]
 for (wx,wz),(ax,az,bx,bz) in zip(worlds,corrections):
  x=(wx+camera[9])*camera[0]+(wz+camera[11])*camera[6]
  z=(wx+camera[9])*camera[2]+(wz+camera[11])*camera[8]
  points.append((x+(1-alpha)*ax+alpha*bx,z+(1-alpha)*az+alpha*bz))
 if any(p[1]>0x5fff for p in points):return None
 if any(not -32768<=v<32768 for p in points for v in p):raise ValueError('Unsupported sampled wall coordinate wrap')
 return tuple(points),old_fixed,new_fixed

@lru_cache(maxsize=512)
def _height_endpoint_terms(ring,offsets,first,old_height,new_height):
 v=ring[first*68:(first+1)*68];terms=[]
 for offset in (8,12,10,14):
  raw=struct.unpack_from('<H',v,offset)[0]
  if struct.unpack_from('<H',v,42)[0]!=65535:raw+=struct.unpack_from('<h',offsets,first*32+(8 if offset in (8,12) else 10))[0]
  terms.append((raw,signed16(raw+old_height)-(raw+old_height),signed16(raw+new_height)-(raw+new_height)))
 return tuple(terms)

def sampled_edge(wall,ring,old_camera,new_camera,camera,endpoints,alpha,offsets=None):
 offsets=bytes(len(ring)//68*32) if offsets is None else offsets
 if len(offsets)!=len(ring)//68*32:raise ValueError('Incomplete sampled wall offsets')
 if alpha==0:return endpoint_edge(wall,ring,old_camera,offsets)
 if alpha==1:return endpoint_edge(wall,ring,new_camera,offsets)
 if not 0<alpha<1:raise ValueError('Invalid sampled wall alpha')
 sampled=_sampled_ring_points(bytes(ring),bytes(offsets),bytes(old_camera),bytes(new_camera),tuple(camera),tuple(tuple(m) for m in endpoints),alpha)
 if sampled is None:return None
 points,old_fixed,new_fixed=sampled
 first=wall.edge;second=(first+1)%len(points);v=ring[first*68:(first+1)*68]
 height=camera[10]+(1-alpha)*(old_fixed[10]-endpoints[0][10])+alpha*(new_fixed[10]-endpoints[1][10])
 ys=[]
 for raw,delta_a,delta_b in _height_endpoint_terms(ring,offsets,first,old_fixed[10],new_fixed[10]):
  y=raw+height
  y+=(1-alpha)*delta_a+alpha*delta_b
  ys.append(y)
 return points[first][0],points[second][0],points[first][1],points[second][1],*ys
