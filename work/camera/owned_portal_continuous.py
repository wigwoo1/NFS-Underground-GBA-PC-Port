"""Integer-cell extension of recovered portal arithmetic, from raw camera-space inputs."""
import math
from owned_portal_transform import signed32
def blend(a,b,fraction):
 # Difference form preserves equal integer-cell values exactly. A weighted
 # sum can create a sub-ULP positive aperture and repeat a closed portal cycle.
 return a if a==b or fraction==0 else b if fraction==1 else a+(b-a)*fraction

def cells(values,operation):
 base=[math.floor(x) for x in values];frac=[x-b for x,b in zip(values,base)]
 def sample(index,arguments):
  if index==len(base):return operation(*arguments)
  left=sample(index+1,arguments+(base[index],))
  if frac[index]==0:return left
  return blend(left,sample(index+1,arguments+(base[index]+1,)),frac[index])
 return sample(0,())

def near_delta(travel,span,difference,reciprocal):
 if span<1 or travel<0 or span>=len(reciprocal)-1:raise ValueError('Portal near interval outside recovered domain')
 t=math.floor(travel);d=math.floor(span);x=math.floor(difference)
 ft=travel-t;fd=span-d;fx=difference-x
 def at_span(ti,di):
  factor=signed32(reciprocal[di])
  a=signed32((signed32(ti*x)*factor)>>24)
  if fx==0:return a
  return blend(a,signed32((signed32(ti*(x+1))*factor)>>24),fx)
 def at_travel(ti):
  a=at_span(ti,d)
  return a if fd==0 else blend(a,at_span(ti,d+1),fd)
 a=at_travel(t)
 return a if ft==0 else blend(a,at_travel(t+1),ft)
def coordinate(x,z,scale,center,reciprocal):
 if z<1 or z>=len(reciprocal)-1:raise ValueError('Portal projection depth outside recovered domain')
 # Same four integer cells and multilinear weights as cells((x,z)).
 # Depth factors are shared by both horizontal cells.
 vx=math.floor(x);dz=math.floor(z);fx=x-vx;fz=z-dz
 a=signed32(reciprocal[dz]*scale)>>7;b=signed32(reciprocal[dz+1]*scale)>>7
 left=blend(center+(signed32(a*(vx>>1))>>16),center+(signed32(b*(vx>>1))>>16),fz)
 right=blend(center+(signed32(a*((vx+1)>>1))>>16),center+(signed32(b*((vx+1)>>1))>>16),fz)
 return blend(left,right,fx)

def projection_depth(z,scale,reciprocal):
 if z<1 or z>=len(reciprocal)-1:raise ValueError('Portal projection depth outside recovered domain')
 dz=math.floor(z)
 return signed32(reciprocal[dz]*scale)>>7,signed32(reciprocal[dz+1]*scale)>>7,z-dz

def coordinate_at_depth(x,depth,center):
 a,b,fz=depth;vx=math.floor(x);fx=x-vx
 left=blend(center+(signed32(a*(vx>>1))>>16),center+(signed32(b*(vx>>1))>>16),fz)
 # Adjacent even/odd x cells use the same arithmetic right-shift value.
 # Their projected results are identical, including signed wrap; blend
 # would return left exactly, so avoid evaluating the duplicate cell.
 if fx==0 or vx&1==0:return left
 right=blend(center+(signed32(a*((vx+1)>>1))>>16),center+(signed32(b*((vx+1)>>1))>>16),fz)
 return blend(left,right,fx)

def edge(a,b,near,scale,center,reciprocal,flip=False):
 x,z=a;nx,nz=b
 if z<near and nz<near:return None
 flags=0
 if z<near:x+=near_delta(near-z,nz-z,nx-x,reciprocal);z=near;flags|=8
 elif nz<near:nx-=near_delta(near-nz,z-nz,nx-x,reciprocal);nz=near;flags|=16
 left,right=coordinate(x,z,scale,center,reciprocal),coordinate(nx,nz,scale,center,reciprocal)
 if flip and left>right:left,right=right,left
 return left,right,flags,z,nz
