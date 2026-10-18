import ctypes as C,struct
from pathlib import Path
from functools import lru_cache
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('ring-correction-batch.dll').resolve()));d.nf_ring_corrections.argtypes=[C.c_char_p,C.c_char_p,C.c_size_t,C.c_char_p,C.c_char_p,C.POINTER(C.c_double),C.POINTER(C.c_int32),C.POINTER(C.c_double)];return d
@lru_cache(maxsize=32)
def corrections(ring,offsets,old_camera,new_camera,endpoints):
 n=len(ring)//68
 if not 0<n<=32 or len(ring)!=n*68 or len(offsets)!=n*32 or len(old_camera)!=48 or len(new_camera)!=48 or len(endpoints)!=2 or any(len(m)!=12 for m in endpoints):raise ValueError('Incomplete ring correction inputs')
 e=(C.c_double*24)(*(x for m in endpoints for x in m));world=(C.c_int32*(n*2))();delta=(C.c_double*(n*4))()
 status=helper().nf_ring_corrections(ring,offsets,n,old_camera,new_camera,e,world,delta)
 if status==-1:raise ValueError('Unsupported sampled world offset wrap')
 if status!=1:raise ValueError('Native ring correction rejected')
 return tuple((world[i*2],world[i*2+1]) for i in range(n)),tuple(tuple(delta[i*4+j] for j in range(4)) for i in range(n)),struct.unpack('<12i',old_camera),struct.unpack('<12i',new_camera)
