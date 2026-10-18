import ctypes as C
from pathlib import Path
from functools import lru_cache
_library=C.CDLL(str(Path(__file__).with_name('owned-wall-point-batch.dll').resolve()))
_call=_library.nf_owned_wall_point_batch
_call.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_double,C.c_void_p]
@lru_cache(maxsize=32)
def buffers(worlds,corrections):
 return (C.c_double*(2*len(worlds)))(*(v for p in worlds for v in p)),(C.c_double*(4*len(worlds)))(*(v for p in corrections for v in p))
def sampled_points(worlds,corrections,camera,alpha):
 w,c=buffers(worlds,corrections);m=(C.c_double*12)(*camera);out=(C.c_double*(2*len(worlds)))()
 if _call(w,c,len(worlds),m,alpha,out)!=1:raise ValueError('Native wall point batch rejected inputs')
 return tuple((out[i*2],out[i*2+1]) for i in range(len(worlds)))
