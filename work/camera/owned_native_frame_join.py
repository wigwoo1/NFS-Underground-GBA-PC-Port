"""Experimental frame assembly into a private unpublished CPython bytes object.
PyBytes_FromStringAndSize(NULL,n) expressly permits filling a new bytes buffer.
No pointer survives this synchronous call; native memcpy runs without the GIL.
"""
import ctypes as C,time,threading
from pathlib import Path
from functools import lru_cache
from owned_thread_cycles import read as thread_cycles
class Span(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
@lru_cache(maxsize=1)
def helper():
 d=C.CDLL(str(Path(__file__).with_name('native-frame-join.dll').resolve()));d.nf_frame_join.argtypes=[C.POINTER(Span),C.c_size_t,C.c_void_p,C.c_size_t];d.nf_frame_join_timed.argtypes=[C.POINTER(Span),C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p];return d
create=C.pythonapi.PyBytes_FromStringAndSize;create.argtypes=[C.c_void_p,C.c_ssize_t];create.restype=C.py_object
pointer=C.pythonapi.PyBytes_AsString;pointer.argtypes=[C.py_object];pointer.restype=C.c_void_p

_local=threading.local()
def trace():return getattr(_local,'last',None)

def join_frame(header,geometry,base,tailoffset):
 cpu_started=time.thread_time_ns();cycles_started=thread_cycles();started=time.perf_counter_ns()
 if not isinstance(header,bytes) or not isinstance(base,bytes) or not 0<=tailoffset<=len(base):raise ValueError('Invalid frame span ownership')
 records=(header,*geometry)
 if not all(isinstance(x,bytes) for x in records) or len(records)+1>4096:raise ValueError('Invalid immutable geometry spans')
 total=sum(map(len,records))+len(base)-tailoffset
 if not 0<total<=64*1024*1024:raise ValueError('Unbounded frame output')
 spans=(Span*(len(records)+1))()
 for i,record in enumerate(records):
  span=spans[i];span.data=pointer(record);span.size=len(record)
 tail=spans[-1];tail.data=pointer(base)+tailoffset;tail.size=len(base)-tailoffset
 packed=time.perf_counter_ns();cpu_packed=time.thread_time_ns();cycles_packed=thread_cycles()
 output=create(None,total)
 allocated=time.perf_counter_ns();cpu_allocated=time.thread_time_ns();cycles_allocated=thread_cycles();timing=(C.c_uint64*5)()
 if helper().nf_frame_join_timed(spans,len(spans),pointer(output),total,timing)!=1:raise ValueError('Native frame assembly rejected')
 completed=time.perf_counter_ns();cpu_completed=time.thread_time_ns();cycles_completed=thread_cycles()
 _local.last=dict(bytes=total,span_count=len(spans),packing_ns=packed-started,allocation_ns=allocated-packed,native_call_ns=completed-allocated,native_boundary=list(timing),stage_thread_cpu_ns=[cpu_packed-cpu_started,cpu_allocated-cpu_packed,cpu_completed-cpu_allocated],stage_thread_cycles=[cycles_packed-cycles_started,cycles_allocated-cycles_packed,cycles_completed-cycles_allocated])
 return output
