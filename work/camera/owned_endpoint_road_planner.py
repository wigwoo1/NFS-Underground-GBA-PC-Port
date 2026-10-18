"""Persistent endpoint raw road submission and GPU record planner.
No sampled motion implementation: callers advance original scene boundaries only.
"""
import ctypes as C,struct,threading,time
from owned_thread_cycles import read as thread_cycles
from pathlib import Path
from owned_road_asset_cache import RoadAssetCache
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_selection import endpoint_road_span_candidates
from owned_complete_road_gpu import encode_road
_road_run_output_local=threading.local()
def road_run_output():
 # Synchronous native writes are consumed before the next call; scratch history
 # remains private to each planner. Separate threads never share output storage.
 output=getattr(_road_run_output_local,'output',None)
 if output is None:
  output=(C.c_uint32*(8192*17))();_road_run_output_local.output=output
 return output

class EndpointRoadPlanner:
 def __init__(self,rom,reciprocal):
  self.rom=bytes(rom);self.reciprocal=tuple(reciprocal);self.assets=RoadAssetCache(self.rom)
  d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nf_road_scratch_create.restype=C.c_void_p;d.nf_road_scratch_destroy.argtypes=[C.c_void_p];d.nf_road_source_runs.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];self.ct=(C.c_uint32*32768)(*reciprocal);self.d=d;self.scratch=None;self.epoch=None;self.refresh=None
 def fork(self):
  if not self.scratch:raise ValueError('Cannot fork uninitialized road history')
  copy=object.__new__(EndpointRoadPlanner)
  copy.assets=self.assets.fork();copy.rom=self.rom;copy.reciprocal=self.reciprocal;copy.ct=self.ct;copy.d=self.d;copy.scratch=None;copy.epoch=None;copy.refresh=None
  self.d.nf_road_scratch_clone.argtypes=[C.c_void_p];self.d.nf_road_scratch_clone.restype=C.c_void_p
  copy.scratch=self.d.nf_road_scratch_clone(self.scratch)
  if not copy.scratch:raise ValueError('Road scratch clone failed')
  copy.epoch=self.epoch;copy.refresh=self.refresh
  return copy
 def close(self):
  if self.scratch:self.d.nf_road_scratch_destroy(self.scratch)
  self.scratch=None;self.epoch=None;self.refresh=None;self.assets.clear()
 def plan(self,c,assets=None):
  self.plan_stages=[];self.plan_stage_dropped=0
  started=time.perf_counter_ns();cycles=thread_cycles()
  def stage(name,descriptor=None):
   nonlocal started,cycles
   now=time.perf_counter_ns();current=thread_cycles()
   if len(self.plan_stages)<512:self.plan_stages.append(dict(name=name,descriptor=descriptor,started_ns=started,completed_ns=now,wall_ns=now-started,thread_cycles=current-cycles))
   else:self.plan_stage_dropped+=1
   started=now;cycles=current
  if self.epoch!=c.epoch:self.close();self.scratch=self.d.nf_road_scratch_create();self.epoch=c.epoch
  if not self.scratch:raise ValueError('Road scratch allocation failed')
  if self.refresh is not None and c.refresh<=self.refresh:raise ValueError('Road planner requires increasing scene refresh')
  if assets is None:
   _,_,m,sources=self.assets.get(c)
  else:
   owner,owned_rom,m,sources=assets
   if owner is not c or owned_rom is not self.rom:raise ValueError('Road asset ownership mismatch')
  stage('asset_acquisition')
  selection_trace=[]
  candidates=endpoint_road_span_candidates(c,m,sources,self.reciprocal,include_empty=True,trace=selection_trace)
  stage('endpoint_selection')
  self.plan_stages[-1]['selection_stages']=selection_trace
  actual=[];details=[];state=c.graph.context[:256]
  try:
   for item in candidates:
    x=item['source'];mat=bytearray(48);struct.pack_into('<HHI',mat,36,struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0],struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',x.material,4)[0]);bounds=(C.c_uint16*4)(*item['bounds']);uv=(C.c_uint32*2)(*(v&0xffffffff for v in struct.unpack_from('<hh',x.animation,4)));out=road_run_output()
    n=C.c_uint();missing=C.c_uint64()
    stage("argument_packing",item["descriptor"])
    ok=self.d.nf_road_source_runs(self.scratch,x.vertices,len(x.vertices),x.offsets,len(x.offsets),x.face,bytes(mat),len(x.vertices)//68,item['affine'],c.graph.context[256:304],bounds,struct.unpack_from('<I',state,108)[0],item['input_count'],self.ct,struct.unpack_from('<I',c.graph.context,304)[0],item['orientation'],uv,out,8192,C.byref(n),C.byref(missing))
    stage('native_source_runs',item['descriptor'])
    key=(item['descriptor'],item['ordinal'],tuple(item['bounds']))
    if not ok:raise ValueError('Raw road source reconstruction failed')
    left,right,top,bottom=item['bounds']
    empty=left>right or top>bottom
    # Original run reconstruction must still advance scratch history for an
    # empty interval. Only the GPU draw is absent, proved by zero source runs.
    if empty and (item['spans'] or n.value):raise ValueError('Empty road interval produced source runs')
    if not missing.value and not empty:actual.append(dict(item,record=encode_road(c.graph.context,x,item['bounds']),runs=n.value))
    details.append(dict(descriptor=x.descriptor,runs=n.value,missing=missing.value,empty_interval=empty,bounds=tuple(item['bounds'])))
    stage('validation_and_encoding',item['descriptor'])
  except Exception:
   self.close();raise
  self.refresh=c.refresh
  return tuple(actual),tuple(details)
