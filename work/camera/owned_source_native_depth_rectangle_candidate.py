"""Candidate determinant correction from owned original model source arithmetic.
No vertex/raster positions are interpolated here; this only samples face decisions.
Near-plane transitions and zero-determinant temporal policy remain unverified.
"""
import ctypes as C,math,struct
from owned_model_projection_cells_candidate import project_camera_cells
from pathlib import Path
_projection_lib=C.CDLL(str(Path(__file__).with_name("source-model-project-cells-candidate.dll")))
_project=_projection_lib.nf_source_model_project_cells
_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p]
import os
if os.environ.get('NFSUG_SOURCE_PROJECTION_CALL_TRACE')=='1':
 from owned_source_projection_call_trace import measure
 _native_project=_project
 def _project(*args):return measure(_native_project,*args)

MatrixBuffer=C.c_double*12
CenterBuffer=C.c_int32*2

def determinant(points):
 a,b,c=points[:3];return (b[1]-a[1])*(c[0]-a[0])-(c[1]-a[1])*(b[0]-a[0])

class OwnedProjectionTable:
 """Private snapshot shared by classifiers; caller arrays are never borrowed."""
 def __init__(self,values):
  self.values=tuple(values)
  if len(self.values)!=32768 or any(not isinstance(v,int) or not 0<=v<=0xffffffff for v in self.values):raise ValueError('Invalid projection table')
  self.native=(C.c_uint32*32768).from_buffer_copy(struct.pack('<32768I',*self.values))

class SourceFaceDeterminants:
 def __init__(self,older,newer,d,table):
  if older['kind']!=3 or newer['kind']!=3 or older['key']!=newer['key']:raise ValueError('Unpaired model source')
  self.table_owner=table if isinstance(table,OwnedProjectionTable) else OwnedProjectionTable(table)
  self.projection_table=self.table_owner.values;self.native_table=self.table_owner.native
  a,b=older['blocks'],newer['blocks']
  if any(bytes(a[k])!=bytes(b[k]) for k in (4,5,6)):raise ValueError('Moving model topology')
  self.native_vertices=C.create_string_buffer(bytes(a[4]));self.vertices=tuple(struct.iter_unpack('<3h',a[4]));self._projection_buffer_type=C.c_double*(2*len(self.vertices));self.faces=[];at=0
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
   if d.nfs_model_project(bytes(blocks[2]),bytes(blocks[4]),len(self.vertices),scale,*center,self.native_table,out)!=1:raise ValueError('Original model projection rejected')
   points=tuple(struct.iter_unpack('<2h',out.raw));self.endpoint_points.append(points);ideal_points=self.projected(m,scale,center);self.projection_residual.append(tuple(tuple(x-y for x,y in zip(a,b)) for a,b in zip(points,ideal_points)));exact=[]
   for ids in self.faces:
    value=int(determinant([points[i] for i in ids]))&0xffffffff;exact.append(value-4294967296 if value&2147483648 else value)
   ideal=tuple(determinant([ideal_points[i] for i in ids]) for ids in self.faces);self.exact.append(tuple(exact));self.residual.append(tuple(x-y for x,y in zip(exact,ideal)))
  if self.scales[0]!=self.scales[1] or self.centers[0]!=self.centers[1]:raise ValueError('Unverified projection parameter transition')
 def projected(self,m,scale,center):
  if len(m)!=12 or not all(math.isfinite(v) for v in m):raise ValueError('Invalid model matrix')
  matrix=MatrixBuffer(*m);center_c=CenterBuffer(*center);out=self._projection_buffer_type()
  if _project(matrix,self.native_vertices,len(self.vertices),scale,center_c,self.native_table,out)!=0:raise ValueError('Unsupported original model coordinate domain')
  return tuple((out[i*2],out[i*2+1]) for i in range(len(self.vertices)))
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

 def combined_decisions(self,m,alpha,rect):
  """Share one native projection between source face and rectangle decisions."""
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid face fraction')
  points=self.projected(m,self.scales[0],self.centers[0])
  faces=tuple(determinant([points[i] for i in ids])+(1-alpha)*a+alpha*b>-.5 for ids,a,b in zip(self.faces,*self.residual))
  a,b=self.projection_residual
  corrected=tuple(tuple(v+(1-alpha)*x+alpha*y for v,x,y in zip(point,pa,pb)) for point,pa,pb in zip(points,a,b))
  rectangles=tuple(source_rectangle_classify(corrected,ids,rect) for ids in self.faces)
  return faces,rectangles

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

