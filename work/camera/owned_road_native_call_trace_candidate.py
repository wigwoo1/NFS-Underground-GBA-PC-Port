"""Optional per-clip native call elapsed/cycle provenance; no ABI replacement."""
import time,os,ctypes as C
from pathlib import Path
from functools import lru_cache
@lru_cache(maxsize=1)
def inside_library():
 d=C.CDLL(str(Path(__file__).with_name("road-inside-call-trace.dll")))
 d.nf_trace_camera.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
 d.nf_trace_clip.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
 return d
from owned_thread_cycles import read
class Call:
 def __init__(self,fn,name,rows):object.__setattr__(self,'fn',fn);object.__setattr__(self,'name',name);object.__setattr__(self,'rows',rows)
 def __getattr__(self,name):return getattr(self.fn,name)
 def __setattr__(self,name,value):setattr(self.fn,name,value)
 def __call__(self,*args):
  native=None;thunk=None;pointer=None
  if os.environ.get("NFSUG_ROAD_NATIVE_INSIDE_TRACE")=="1" and self.name in ("nf_road_camera_ring","nf_road_clip_continuous"):
   d=inside_library();thunk=d.nf_trace_camera if self.name=="nf_road_camera_ring" else d.nf_trace_clip;pointer=C.cast(self.fn,C.c_void_p);native=(C.c_uint64*5)()
  start=time.perf_counter_ns();cycles=read()
  try:return self.fn(*args) if thunk is None else thunk(pointer,*args,native)
  finally:
   end=time.perf_counter_ns();last=read();self.rows.append(dict(name=self.name,started_ns=start,completed_ns=end,wall_ns=end-start,thread_cycles=last-cycles,native_inside=None if native is None else dict(qpc_start=native[0],qpc_end=native[2],qpc_frequency=native[4],wall_ns=(native[2]-native[0])*1_000_000_000//native[4],thread_cycles=native[3]-native[1])))
class Library:
 def __init__(self,library,rows):self.library=library;self.rows=rows;self.calls={}
 def __getattr__(self,name):
  if name not in self.calls:self.calls[name]=Call(getattr(self.library,name),name,self.rows)
  return self.calls[name]
