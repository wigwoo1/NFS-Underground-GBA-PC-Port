"""Candidate determinant correction from owned original model source arithmetic.
No vertex/raster positions are interpolated here; this only samples face decisions.
Near-plane transitions and zero-determinant temporal policy remain unverified.
"""
import ctypes as C,math,struct

def determinant(points):
 a,b,c=points[:3];return (b[1]-a[1])*(c[0]-a[0])-(c[1]-a[1])*(b[0]-a[0])

class SourceFaceDeterminants:
 def __init__(self,older,newer,d,table):
  if older['kind']!=3 or newer['kind']!=3 or older['key']!=newer['key']:raise ValueError('Unpaired model source')
  a,b=older['blocks'],newer['blocks']
  if any(bytes(a[k])!=bytes(b[k]) for k in (4,5,6)):raise ValueError('Moving model topology')
  self.vertices=tuple(struct.iter_unpack('<3h',a[4]));self.faces=[];at=0
  for n in a[5]:
   if n<3 or n>32:raise ValueError('Invalid model face')
   ids=struct.unpack_from('<'+str(n)+'H',a[6],at*2);at+=n
   if any(i>=len(self.vertices) for i in ids):raise ValueError('Invalid model index')
   self.faces.append(ids)
  if at*2!=len(a[6]):raise ValueError('Incomplete face topology')
  self.endpoint_points=[];self.projection_residual=[];self.matrices=[];self.exact=[];self.residual=[];self.centers=[];self.scales=[]
  d.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p]
  for blocks in (a,b):
   matrix=struct.unpack('<12i',blocks[2]);m=tuple(v/16384 if i<9 else float(v) for i,v in enumerate(matrix));self.matrices.append(m)
   scale=struct.unpack_from('<I',blocks[0],64)[0];center=struct.unpack_from('<2h',blocks[3],8);self.centers.append(center);self.scales.append(scale)
   out=C.create_string_buffer(len(self.vertices)*4)
   if d.nfs_model_project(bytes(blocks[2]),bytes(blocks[4]),len(self.vertices),scale,*center,table,out)!=1:raise ValueError('Original model projection rejected')
   points=tuple(struct.iter_unpack('<2h',out.raw));self.endpoint_points.append(points);ideal_points=self.projected(m,scale,center);self.projection_residual.append(tuple(tuple(x-y for x,y in zip(a,b)) for a,b in zip(points,ideal_points)));exact=[]
   for ids in self.faces:
    value=int(determinant([points[i] for i in ids]))&0xffffffff;exact.append(value-4294967296 if value&2147483648 else value)
   ideal=self.ideal(m,scale,center);self.exact.append(tuple(exact));self.residual.append(tuple(x-y for x,y in zip(exact,ideal)))
  if self.scales[0]!=self.scales[1] or self.centers[0]!=self.centers[1]:raise ValueError('Unverified projection parameter transition')
 def projected(self,m,scale,center):
  if len(m)!=12 or not all(math.isfinite(v) for v in m):raise ValueError('Invalid model matrix')
  points=[]
  for local in self.vertices:
   v=[m[9+k]+sum(local[j]*m[j*3+k] for j in range(3)) for k in range(3)]
   if not 64<=v[2]<=24576:raise ValueError('Unverified near/depth transition')
   points.append((center[0]+scale*v[0]/v[2],center[1]+scale*v[1]/v[2]))
  return tuple(points)
 def ideal(self,m,scale,center):
  points=self.projected(m,scale,center)
  return tuple(determinant([points[i] for i in ids]) for ids in self.faces)
 def sample(self,m,alpha):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid face fraction')
  ideal=self.ideal(m,self.scales[0],self.centers[0])
  return tuple(x+(1-alpha)*a+alpha*b for x,a,b in zip(ideal,*self.residual))

 def decisions(self,m,alpha):
  # Original signed integer determinant draws 0 and rejects -1.
  # Mid-cell extension places the continuous threshold halfway between them.
  # This preserves all integer decisions; fractional policy needs GPU validation.
  return tuple(value>-.5 for value in self.sample(m,alpha))

 def rectangle_decisions(self,m,alpha,rect):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid rectangle fraction')
  points=self.projected(m,self.scales[0],self.centers[0])
  a,b=self.projection_residual
  corrected=tuple(tuple(v+(1-alpha)*x+alpha*y for v,x,y in zip(point,pa,pb)) for point,pa,pb in zip(points,a,b))
  return tuple(source_rectangle_classify(corrected,ids,rect) for ids in self.faces)

def source_rectangle_classify(points,indices,rect):
 # Classification coordinates only, never raster positions or fitted polygons.
 # Mid-cell boundaries preserve original integer left/top inclusive,
 # right/bottom exclusive membership. Fractional policy remains a candidate.
 if len(rect)!=4 or not all(math.isfinite(v) for v in rect):raise ValueError('Invalid rectangle')
 if not indices or len(indices)>32:raise ValueError('Invalid rectangle face')
 flags=0;inside_x=inside_y=False
 for index in indices:
  if not 0<=index<len(points):raise ValueError('Invalid rectangle vertex')
  x,y=points[index]
  if not math.isfinite(x) or not math.isfinite(y):raise ValueError('Nonfinite rectangle point')
  ix=rect[0]-.5<=x<rect[2]-.5;iy=rect[1]-.5<=y<rect[3]-.5
  inside_x|=ix;inside_y|=iy
  if not ix:flags|=1
  if not iy:flags|=2
 return flags if inside_x and inside_y else 4
