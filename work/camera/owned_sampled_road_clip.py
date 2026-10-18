"""Camera-space road projection/clipping on caller-owned isolated scratch.
Caller must supply recovered surface stream input_count; sampled count ownership
is a separate requirement, never silently inferred from projected ring length.
"""
import ctypes as C,os
from functools import lru_cache
@lru_cache(maxsize=64)
def camera_buffer_type(amount):return C.c_double*amount
# Retain fixed array classes; each invocation still owns fresh buffers.
PointsBuffer=C.c_double*320
RingBuffer=C.c_double*384
ClipBuffer=C.c_double*768
ProjectionBuffer=C.c_int32*3
class Attributes(C.Structure):
 _fields_=[('count',C.c_uint32),('shift',C.c_uint32),('height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('uv',(C.c_int32*2)*32)]
def clipped_camera_road(d,scratch,camera,attributes,bounds,base,input_count,table,*,commit_branch=False):
 native_trace=None
 if os.environ.get("NFSUG_ROAD_NATIVE_CALL_TRACE")=="1":
  from owned_road_native_call_trace_candidate import Library
  native_trace=[];d=Library(d,native_trace)
 n=attributes.count
 if len(camera)!=n*3 or len(bounds)!=4 or not 0<=input_count<=64:raise ValueError('Incomplete road projection ownership')
 d.nf_road_camera_ring.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 d.nf_road_scratch_ring.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
 d.nf_road_clip_continuous.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
 d.nf_road_scratch_commit.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint]
 d.nf_road_scratch_clone.argtypes=[C.c_void_p];d.nf_road_scratch_clone.restype=C.c_void_p;d.nf_road_scratch_destroy.argtypes=[C.c_void_p]
 temporary=d.nf_road_scratch_clone(scratch)
 if not temporary:raise ValueError('Missing road history')
 try:
  points=PointsBuffer();ring=RingBuffer();out=ClipBuffer();count=C.c_uint();amount=C.c_uint();missing=C.c_uint64();projection=ProjectionBuffer(120,87,128);positions=camera_buffer_type(len(camera))(*camera)
  if not d.nf_road_camera_ring(positions,n,C.byref(attributes),projection,table,points,64,C.byref(count)):raise ValueError('Road camera ring projection failed')
  if not d.nf_road_scratch_ring(temporary,base,points,count.value,attributes.affine,ring,C.byref(missing)):raise ValueError('Road depth ownership failed')
  if not d.nf_road_clip_continuous(ring,count.value,bounds[0],bounds[1],table,out,128,C.byref(amount)):raise ValueError('Road fractional clipping failed')
  if not d.nf_road_scratch_commit(temporary,base,input_count,out,amount.value):raise ValueError('Road scratch placement failed')
  if commit_branch:
   d.nf_road_scratch_assign.argtypes=[C.c_void_p,C.c_void_p]
   if not d.nf_road_scratch_assign(scratch,temporary):raise ValueError('Road branch commit failed')
  result=dict(ring=tuple(out[:amount.value*6]),count=amount.value,projected_count=count.value,missing=missing.value)
  if native_trace is not None:result["native_call_trace"]=native_trace
  return result
 finally:d.nf_road_scratch_destroy(temporary)
