import ctypes as C
from pathlib import Path
from functools import lru_cache
from owned_continuous_wall_visibility import _ring_endpoint_corrections
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('ring-sample-batch.dll').resolve()));d.nf_sample_ring_points.argtypes=[C.POINTER(C.c_int32),C.POINTER(C.c_double),C.c_size_t,C.POINTER(C.c_double),C.c_double,C.POINTER(C.c_double)];return d
@lru_cache(maxsize=32)
def inputs(worlds,corrections):
 return (C.c_int32*(len(worlds)*2))(*(v for p in worlds for v in p)),(C.c_double*(len(corrections)*4))(*(v for p in corrections for v in p))
@lru_cache(maxsize=32)
def sample(ring,offsets,old_camera,new_camera,camera,endpoints,alpha):
 worlds,corrections,a,b=_ring_endpoint_corrections(ring,offsets,old_camera,new_camera,endpoints)
 n=len(worlds)
 if not 0<n<=32 or len(camera)!=12:raise ValueError('Incomplete sampled ring inputs')
 packed,delta=inputs(worlds,corrections);cam=(C.c_double*12)(*camera);out=(C.c_double*(n*2))()
 status=helper().nf_sample_ring_points(packed,delta,n,cam,alpha,out)
 if status==2:return None
 if status==-1:raise ValueError('Unsupported sampled wall coordinate wrap')
 if status!=1:raise ValueError('Native sampled ring rejected')
 return tuple((out[i*2],out[i*2+1]) for i in range(n)),a,b
