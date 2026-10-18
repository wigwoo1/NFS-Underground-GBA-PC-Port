"""Continuous extension of recovered wall visibility arithmetic, independent of raster draw."""
import struct,math
from dataclasses import dataclass
from owned_portal_continuous import cells,coordinate
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
   return cells((travel,span,difference),lambda t,s,d:(int(d)*((int(t)*reciprocal[int(s)])&0xffffffff))>>24)
  adjustment=delta(nx-x)
  if start:x+=adjustment;z=near;flags|=8
  else:nx-=adjustment;nz=near;flags|=16
  for a,b in ((0,1),(2,3)):
   adjustment=delta(ys[b]-ys[a])
   if start:ys[a]+=adjustment
   else:ys[b]-=adjustment
 left,right=coordinate(x,z,scale,cx,reciprocal),coordinate(nx,nz,scale,cx,reciprocal)
 if flags&0x2000 and right<left:flags|=2
 if flags&2:left,right=right,left
 if right<=left or right<bounds[0] or left>=bounds[1]:return WallVisibility(False,'viewport_rejected',(left,right),(),flags|4)
 y=tuple(coordinate(v,z if i%2==0 else nz,scale,cy,reciprocal) for i,v in enumerate(ys))
 if y[0]>=bounds[3] and y[1]>=bounds[3] and y[2]<bounds[2] and y[3]<bounds[2]:return WallVisibility(False,'vertical_rejected',(left,right),y,flags)
 return WallVisibility(True,'visible',(left,right),y,flags)

def endpoint_edge(wall,ring,camera):
 ok,raw=transform(ring,bytes(len(ring)//68*32),camera)
 if not ok:return None
 scratch=raw[wall.edge*52:(wall.edge+1)*52]
 return (*struct.unpack_from('<4h',scratch),*struct.unpack_from('<4h',scratch,8))

def sampled_edge(wall,ring,old_camera,new_camera,camera,endpoints,alpha):
 if alpha==0:return endpoint_edge(wall,ring,old_camera)
 if alpha==1:return endpoint_edge(wall,ring,new_camera)
 if not 0<alpha<1:raise ValueError('Invalid sampled wall alpha')
 if any(struct.unpack_from('<H',ring,i+42)[0]!=65535 for i in range(0,len(ring),68)):raise ValueError('Unsupported sampled wall offsets')
 def continuous(m):
  points=[]
  for i in range(0,len(ring),68):
   x,z=struct.unpack_from('<2i',ring,i);points.append(((x+m[9])*m[0]+(z+m[11])*m[6],(x+m[9])*m[2]+(z+m[11])*m[8]))
  return points
 old_fixed=struct.unpack('<12i',old_camera);new_fixed=struct.unpack('<12i',new_camera)
 from owned_portal_transform import transform as fixed_transform
 a=continuous(endpoints[0]);b=continuous(endpoints[1]);current=continuous(camera);points=[]
 for i,(x,z) in enumerate(current):
  world=struct.unpack_from('<2i',ring,i*68);fa=fixed_transform(*world,old_fixed);fb=fixed_transform(*world,new_fixed)
  points.append((x+(1-alpha)*(fa[0]-a[i][0])+alpha*(fb[0]-b[i][0]),z+(1-alpha)*(fa[1]-a[i][1])+alpha*(fb[1]-b[i][1])))
 if any(p[1]>0x5fff for p in points):return None
 if any(not -32768<=v<32768 for p in points for v in p):raise ValueError('Unsupported sampled wall coordinate wrap')
 first=wall.edge;second=(first+1)%len(points);v=ring[first*68:(first+1)*68]
 height=camera[10]+(1-alpha)*(old_fixed[10]-endpoints[0][10])+alpha*(new_fixed[10]-endpoints[1][10])
 ys=[]
 for offset in (8,12,10,14):
  raw=struct.unpack_from('<H',v,offset)[0]
  ya=signed16(raw+old_fixed[10]);yb=signed16(raw+new_fixed[10]);y=raw+height
  y+=(1-alpha)*(ya-(raw+old_fixed[10]))+alpha*(yb-(raw+new_fixed[10]))
  ys.append(y)
 return points[first][0],points[second][0],points[first][1],points[second][1],*ys
