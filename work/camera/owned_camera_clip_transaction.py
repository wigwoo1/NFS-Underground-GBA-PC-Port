"""Experimental single native dispatch; probe DLL retained by per-library owner."""
import ctypes as C
from pathlib import Path
from functools import lru_cache
from owned_sampled_road_clip import ClipBuffer,camera_buffer_type
BoundsBuffer=C.c_double*4
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('road-camera-clip-transaction.dll').resolve()))
 d.nf_camera_clip_transaction.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint,C.c_void_p,C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
 return d

def clipped_camera_road(d,scratch,camera,attributes,bounds,base,input_count,table,*,commit_branch=False):
 n=attributes.count
 if len(camera)!=n*3 or len(bounds)!=4 or not 0<=input_count<=64:raise ValueError('Incomplete road projection ownership')
 if not hasattr(d,'_camera_clip_functions'):
  names=('nf_road_scratch_clone','nf_road_scratch_destroy','nf_road_camera_ring','nf_road_scratch_ring','nf_road_clip_continuous','nf_road_scratch_commit','nf_road_scratch_assign')
  d._camera_clip_functions=(C.c_void_p*7)(*(C.cast(getattr(d,name),C.c_void_p).value for name in names))
 out=ClipBuffer();positions=camera_buffer_type(len(camera))(*camera);clipbounds=BoundsBuffer(*bounds);count=C.c_uint();amount=C.c_uint();missing=C.c_uint64()
 if not helper().nf_camera_clip_transaction(d._camera_clip_functions,scratch,positions,n,C.byref(attributes),clipbounds,base,input_count,table,int(commit_branch),out,128,C.byref(count),C.byref(amount),C.byref(missing)):raise ValueError('Native road clip transaction failed')
 return dict(ring=tuple(out[:amount.value*6]),count=amount.value,projected_count=count.value,missing=missing.value)
