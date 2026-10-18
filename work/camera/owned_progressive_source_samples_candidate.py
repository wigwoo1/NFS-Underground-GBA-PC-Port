"""Privately owned source masks and anchored frames prepared before GPU handoff."""
import ctypes as C,struct,time,math,json
from pathlib import Path
from owned_source_presentation_batch_candidate import prepare_source_models,rigid_camera
from owned_source_face_mask_candidate import build_source_face_mask
from functools import lru_cache
from owned_thread_cycles import read as thread_cycles
from owned_source_native_depth_rectangle_candidate import OwnedProjectionTable
@lru_cache(maxsize=1)
def projection_table_owner():
 return OwnedProjectionTable(struct.unpack('<32768I',Path(__file__).with_name('road-correction-reciprocal.bin').read_bytes()[:131072]))

@lru_cache(maxsize=1)
def source_library_owner():
 return C.CDLL(str(Path(__file__).with_name('owned-sky-source-context-candidate.dll')))

class ProgressiveSourceWorldSamples:
 def __init__(self,prepared,alphas,budget=64*1024*1024,trace=False,on_sample=None):
  self.samples={};self.source_masks={};self.bytes=0;self.sample_timings=[];self.prepared_close_ns=None;self.source_setup_stages=[]
  try:
   if not 1<=len(alphas)<=8:raise ValueError('Unbounded source sample count')
   plan,_,pa,pb,*_=prepared.pair.portal.motion.arguments
   self.source_cameras=(struct.unpack('<12i',plan['camera_older']),struct.unpack('<12i',plan['camera_newer']),rigid_camera(pa),rigid_camera(pb))
   gpu=source_library_owner()
   table=projection_table_owner()
   anchors,classifiers=prepare_source_models(prepared,gpu,table,self.source_setup_stages if trace else None)
   for alpha in alphas:
    if not math.isfinite(alpha) or not 0<alpha<1 or alpha in self.samples:raise ValueError('Invalid source sample identity')
    if trace:
     started=time.perf_counter_ns();cpu_started=time.thread_time_ns();cycles_started=thread_cycles();stage_trace=[]
     stage_begin=started;stage_cpu=cpu_started;stage_cycles=cycles_started
     def mark(name):
      nonlocal stage_begin,stage_cpu,stage_cycles
      end=time.perf_counter_ns();cpu=time.thread_time_ns();cycles=thread_cycles()
      stage_trace.append(dict(name=name,started_ns=stage_begin,completed_ns=end,wall_ns=end-stage_begin,thread_cpu_ns=cpu-stage_cpu,thread_cycles=cycles-stage_cycles))
      stage_begin=end;stage_cpu=cpu;stage_cycles=cycles
    frame,camera,models,bounds,detail=prepared.sample(alpha)
    if trace:mark('world_sample')
    anchor_trace=[] if trace else None
    models=anchors.sample(frame,models,alpha,anchor_trace)
    if trace:
     mark('model_anchors');stage_trace[-1]['anchor_stages']=anchor_trace
    packed=build_source_face_mask(frame,models,bounds,alpha,classifiers)
    if trace:mark('source_face_mask')
    self.bytes+=len(frame)+sum(C.sizeof(x) for x in (camera,models,bounds,*packed[:2]))
    if self.bytes>budget:raise ValueError('Prepared source sample budget exceeded')
    self.samples[alpha]=(frame,camera,models,bounds,detail);self.source_masks[alpha]=packed
    if trace:mark('sample_retention')
    if on_sample is not None:
     # Immutable frame owners survive producer close; arrays and details are private bytes.
     packet=(alpha,frame,bytes(camera),bytes(models),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2],json.dumps(detail,sort_keys=True).encode(),json.dumps(packed[3],sort_keys=True).encode(),self.source_cameras)
     if trace:mark('sample_packet_encoding')
     on_sample(packet)
    if trace:
     mark('sample_publication')
     self.sample_timings.append(dict(alpha=alpha,started_ns=started,completed_ns=stage_begin,wall_ns=stage_begin-started,thread_cpu_ns=stage_cpu-cpu_started,thread_cycles=stage_cycles-cycles_started,assembly_stages=list(getattr(prepared.pair,'_last_sample_stages',[])),source_sample_stages=stage_trace,source_classification_prepared=True,source_setup_stages=list(self.source_setup_stages) if len(self.samples)==1 else []))
  except BaseException:self.close();raise
  finally:
   from owned_motion_pairs import _record_cache
   from owned_model_key_records_candidate import _model_record_cache
   _record_cache.entries=[];_model_record_cache.entries=[]
   started=time.perf_counter_ns();prepared.close();self.prepared_close_ns=time.perf_counter_ns()-started
 def sample(self,alpha):
  if alpha not in self.samples:raise ValueError('Unprepared source sample')
  return self.samples[alpha]
 def close(self):
  self.samples.clear();self.source_masks.clear();self.source_cameras=();self.bytes=0

