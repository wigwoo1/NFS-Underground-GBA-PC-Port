"""Owned fixed camera endpoint transforms, batched with exact uint32 arithmetic."""
import ctypes as C
from pathlib import Path
from functools import lru_cache
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('portal-transform-batch.dll').resolve()))
 p=C.POINTER(C.c_int32);d.nf_portal_transform_batch.argtypes=[p,C.c_size_t,p,p,p]
 return d
def transform_pair(points,a,b):
 n=len(points)
 if not 0<n<=32 or len(a)!=12 or len(b)!=12:raise ValueError('Incomplete native transform batch')
 values=tuple(v for point in points for v in point)
 if len(values)!=n*2 or any(not isinstance(v,int) or not -2147483648<=v<=2147483647 for v in (*values,*a,*b)):raise ValueError('Native transform batch outside signed32 domain')
 packed=(C.c_int32*(2*n))(*values);ma=(C.c_int32*12)(*a);mb=(C.c_int32*12)(*b);out=(C.c_int32*(4*n))()
 if helper().nf_portal_transform_batch(packed,n,ma,mb,out)!=1:raise ValueError('Native transform batch rejected')
 return tuple((out[i*4],out[i*4+1],out[i*4+2],out[i*4+3]) for i in range(n))
