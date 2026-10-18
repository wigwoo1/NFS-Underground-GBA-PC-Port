"""Isolated fused road dispatcher with private per-thread reusable buffers."""
import ctypes as C,threading
from owned_camera_road_dispatch import fn
_buffers=threading.local()
def clipped_camera_road(d,scratch,camera,attributes,bounds,base,input_count,table,*,commit_branch=False):
 n=attributes.count
 if len(camera)!=n*3 or len(bounds)!=4 or not 0<=input_count<=64:raise ValueError('Incomplete road projection ownership')
 if not 3<=n<=32:raise ValueError('Invalid bounded road source count')
 values=getattr(_buffers,'values',None)
 if values is None:
  values=((C.c_double*96)(),(C.c_double*768)(),C.c_uint(),C.c_uint(),C.c_uint64());_buffers.values=values
 positions,out,amount,projected,missing=values
 for i,v in enumerate(camera):positions[i]=v
 amount.value=projected.value=missing.value=0
 if not fn(scratch,positions,n,C.byref(attributes),attributes.affine,bounds[0],bounds[1],base,input_count,table,int(commit_branch),out,C.byref(amount),C.byref(projected),C.byref(missing)):raise ValueError('Fused road projection/clipping failed')
 if amount.value>128 or projected.value>64:raise ValueError('Invalid bounded road output')
 return dict(ring=tuple(out[:amount.value*6]),count=amount.value,projected_count=projected.value,missing=missing.value)
