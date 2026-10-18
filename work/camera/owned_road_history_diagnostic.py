"""Diagnostic-only snapshot of the RoadScratch ABI in native_road_source_decode.c."""
import ctypes as C,math
class Scratch(C.Structure):
 _fields_=[('count',C.c_uint),('address',C.c_uint32*512),('depth',C.c_double*512)]
assert Scratch.depth.offset==2056 and C.sizeof(Scratch)==6152

def snapshot(handle):
 if not handle:raise ValueError('Missing native road history')
 value=C.cast(handle,C.POINTER(Scratch)).contents
 if value.count>512:raise ValueError('Invalid native road history count')
 rows=[(int(value.address[i]),float(value.depth[i])) for i in range(value.count)]
 if len({a for a,d in rows})!=len(rows) or any(not math.isfinite(d) for a,d in rows):raise ValueError('Invalid native road history values')
 return dict(abi='RoadScratch-u32-address512-f64-depth512-v1',rows=rows)

def restore(library,payload):
 rows=payload['rows']
 if payload['abi']!='RoadScratch-u32-address512-f64-depth512-v1' or len(rows)>512:raise ValueError('Unsupported road history snapshot')
 if len({a for a,d in rows})!=len(rows) or any(not isinstance(a,int) or not 0<=a<=0xffffffff or not math.isfinite(d) for a,d in rows):raise ValueError('Invalid restored road history values')
 value=Scratch();value.count=len(rows)
 for i,(a,d) in enumerate(rows):value.address[i]=a;value.depth[i]=d
 library.nf_road_scratch_create.restype=C.c_void_p
 handle=library.nf_road_scratch_create()
 if not handle:raise MemoryError('Road history allocation failed')
 C.memmove(handle,C.byref(value),C.sizeof(value));return handle
