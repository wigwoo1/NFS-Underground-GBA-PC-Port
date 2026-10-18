"""Optional fused dispatch, retaining original native clipping and scratch rules."""
import ctypes as C
from pathlib import Path
lib=C.CDLL(str(Path('work/camera/owned-camera-road-dispatch.dll').resolve()))
fn=lib.nf_camera_road_dispatch
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_uint,C.c_uint,C.c_void_p,C.c_int,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
def clipped_camera_road(d,scratch,camera,attributes,bounds,base,input_count,table,*,commit_branch=False):
 n=attributes.count
 if len(camera)!=n*3 or len(bounds)!=4 or not 0<=input_count<=64:raise ValueError('Incomplete road projection ownership')
 positions=(C.c_double*len(camera))(*camera);out=(C.c_double*768)();amount=C.c_uint();projected=C.c_uint();missing=C.c_uint64()
 if not fn(scratch,positions,n,C.byref(attributes),attributes.affine,bounds[0],bounds[1],base,input_count,table,int(commit_branch),out,C.byref(amount),C.byref(projected),C.byref(missing)):raise ValueError('Fused road projection/clipping failed')
 return dict(ring=tuple(out)[:amount.value*6],count=amount.value,projected_count=projected.value,missing=missing.value)
