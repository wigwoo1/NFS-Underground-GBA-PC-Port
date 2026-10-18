import ctypes as C
from pathlib import Path
from functools import lru_cache
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('road-rigid-batch.dll').resolve()));d.nf_road_rigid_batch.argtypes=[C.POINTER(C.c_double),C.c_size_t,C.POINTER(C.c_double),C.POINTER(C.c_double)];d.nf_compensated_sum3.argtypes=[C.c_double]*3;d.nf_compensated_sum3.restype=C.c_double;return d
@lru_cache(maxsize=64)
def world_input(world):return (C.c_double*len(world))(*world)
@lru_cache(maxsize=64)
def rigid_points(world,pose):
 n=len(world)//3
 if len(world)!=n*3 or not 0<n<=32 or len(pose)!=12:raise ValueError('Invalid native rigid road batch')
 p=(C.c_double*12)(*pose);out=(C.c_double*len(world))()
 if helper().nf_road_rigid_batch(world_input(world),n,p,out)!=1:raise ValueError('Native rigid road batch rejected')
 return tuple(out)
