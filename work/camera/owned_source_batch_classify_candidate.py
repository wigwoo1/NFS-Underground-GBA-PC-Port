"""Isolated synchronous source classification with privately owned native arrays."""
import ctypes as C,math
from pathlib import Path
from owned_source_projection_scratch_candidate import SourceFaceDeterminants as Base,_project
_lib=C.CDLL(str(Path(__file__).with_name('source-classify-batch-candidate.dll')))
_classify=_lib.nf_source_classify
P=C.c_void_p;U=C.c_uint
_classify.argtypes=[P,U,P,P,U,U,P,P,P,P,C.c_double,P,P,P]
class SourceFaceDeterminants(Base):
 def __init__(self,*args):
  super().__init__(*args)
  offsets=[0];ids=[]
  for face in self.faces:ids.extend(face);offsets.append(len(ids))
  self._offsets=(C.c_uint32*len(offsets))(*offsets);self._indices=(C.c_uint32*max(1,len(ids)))(*ids);self._index_count=len(ids)
  self._face_residuals=tuple((C.c_double*max(1,len(self.faces)))(*r) for r in self.residual)
  self._point_residuals=tuple((C.c_double*(2*len(self.vertices)))(*(v for point in r for v in point)) for r in self.projection_residual)
  self._faces_out=(C.c_uint8*max(1,len(self.faces)))();self._codes_out=(C.c_uint8*max(1,len(self.faces)))();self._rect=(C.c_double*4)()
 def combined_decisions(self,m,alpha,rect):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid face fraction')
  if len(m)!=12 or not all(math.isfinite(v) for v in m):raise ValueError('Invalid model matrix')
  if len(rect)!=4 or not all(math.isfinite(v) for v in rect):raise ValueError('Invalid rectangle')
  with self._projection_lock:
   for i,v in enumerate(m):self._matrix_buffer[i]=v
   self._center_buffer[0],self._center_buffer[1]=self.centers[0]
   for i,v in enumerate(rect):self._rect[i]=v
   if _project(self._matrix_buffer,self.native_vertices,len(self.vertices),self.scales[0],self._center_buffer,self.native_table,self._projection_buffer)!=0:raise ValueError('Unsupported original model coordinate domain')
   if _classify(self._projection_buffer,len(self.vertices),self._offsets,self._indices,len(self.faces),self._index_count,*self._face_residuals,*self._point_residuals,alpha,self._rect,self._faces_out,self._codes_out)!=0:raise ValueError('Invalid native source classification')
   return tuple(bool(self._faces_out[i]) for i in range(len(self.faces))),tuple(self._codes_out[i] for i in range(len(self.faces)))
