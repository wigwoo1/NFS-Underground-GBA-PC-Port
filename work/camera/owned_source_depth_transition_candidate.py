"""Isolated source classifier for one rejected projection endpoint.
Uses the sole valid endpoint's arithmetic residual; fractional fidelity unverified.
Never projects or clamps coordinates outside the original depth domain.
"""
import ctypes as C,math,struct
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants as Base
class SourceFaceDeterminants(Base):
 def __init__(self,older,newer,d,table):
  self.endpoint_valid=(True,True);self.single_endpoint=False
  try:super().__init__(older,newer,d,table);return
  except ValueError as e:
   if str(e)!='Original model projection rejected':raise
  if older['key']!=newer['key'] or any(bytes(older['blocks'][k])!=bytes(newer['blocks'][k]) for k in (4,5,6)):raise ValueError('Moving model topology')
  rows=(older,newer);valid=[]
  for row in rows:
   b=row['blocks'];count=len(b[4])//6;out=C.create_string_buffer(count*4);scale=struct.unpack_from('<I',b[0],64)[0];center=struct.unpack_from('<2h',b[3],8)
   valid.append(d.nfs_model_project(bytes(b[2]),bytes(b[4]),count,scale,*center,self.native_table,out)==1)
  if sum(valid)!=1:raise ValueError('No valid endpoint calibration for depth transition')
  params=[(struct.unpack_from('<I',r['blocks'][0],64)[0],struct.unpack_from('<2h',r['blocks'][3],8)) for r in rows]
  if params[0]!=params[1]:raise ValueError('Unverified projection parameter transition')
  anchor=rows[valid.index(True)];super().__init__(anchor,anchor,d,table)
  self.endpoint_valid=tuple(valid);self.single_endpoint=True
 def depth_valid(self,m,alpha):
  if not math.isfinite(alpha) or not 0<=alpha<=1 or len(m)!=12 or not all(math.isfinite(v) for v in m):raise ValueError('Invalid depth sample')
  if alpha in (0,1) and not self.endpoint_valid[int(alpha)]:return False
  return all(0<=m[11]+x*m[2]+y*m[5]+z*m[8]<=24576 for x,y,z in self.vertices)
 def combined_decisions(self,m,alpha,rect):
  if self.single_endpoint and not self.depth_valid(m,alpha):return (False,)*len(self.faces),(4,)*len(self.faces)
  return super().combined_decisions(m,alpha,rect)
 def decisions(self,m,alpha):
  if self.single_endpoint and not self.depth_valid(m,alpha):return (False,)*len(self.faces)
  return super().decisions(m,alpha)
 def rectangle_decisions(self,m,alpha,rect):
  if self.single_endpoint and not self.depth_valid(m,alpha):return (4,)*len(self.faces)
  return super().rectangle_decisions(m,alpha,rect)
