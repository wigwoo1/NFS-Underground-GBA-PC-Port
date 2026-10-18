"""Actual child normal-GC census; counts only, no retained source references."""
import types
import owned_fixed_types_process_service_candidate as fixed
from owned_bounded_fixed_types_service_candidate import BoundedProcessService as Base
def request_child(connection,rom,shared_output,request_name):
 import gc,time,json,os,collections,sys
 from pathlib import Path
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants as Original
 policy=(gc.isenabled(),gc.get_threshold());rows=[];constructed=0;projection_types={}
 def census(label):
  started=time.perf_counter_ns();objects=gc.get_objects()
  counts=collections.Counter(type(o).__module__+'.'+type(o).__qualname__ for o in objects)
  arrays=collections.Counter()
  for obj in objects:
   if type(obj).__name__=='PyCArrayType':
    arrays[(getattr(obj,'_length_',None),getattr(getattr(obj,'_type_',None),'__name__',None))]+=1
  caches={}
  for modname,fnname in (('owned_wall_visibility_candidate','batch_types'),('owned_double_array_type','double_array_type'),('owned_source_face_mask_candidate','mask_buffer_types'),('owned_preparation_fixed_types_install_candidate','char_type')):
   module=sys.modules.get(modname);fn=getattr(module,fnname,None)
   if fn is not None and hasattr(fn,'cache_info'):caches[modname+'.'+fnname]=fn.cache_info()._asdict()
  rows.append(dict(label=label,constructed=constructed,tracked=len(objects),counts=dict(counts),cache_stats=caches,array_types=[dict(length=k[0],element=k[1],count=v) for k,v in arrays.items()],duration_ns=time.perf_counter_ns()-started))
 class Census(Original):
  def __init__(self,*args):
   nonlocal constructed
   super().__init__(*args);constructed+=1
   length=self._projection_buffer_type._length_;projection_types.setdefault(length,set()).add(id(self._projection_buffer_type))
   if constructed in (1,40,80,160):census('active')
 batch.SourceFaceDeterminants=Census
 try:fixed.request_child(connection,rom,shared_output,request_name)
 finally:
  assert policy==(gc.isenabled(),gc.get_threshold());census('shutdown')
  Path('work/camera/prototype-runs/child-heap-census-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),constructed=constructed,rows=rows,projection_type_id_counts={k:len(v) for k,v in projection_types.items()},normal_gc_unchanged=True,scope='Actual child tracked object/type counts at classifier construction; IDs only, no source references retained. Instrumented run not cadence qualification.'),indent=2))
class ProcessPreparationService(Base):pass
original=fixed.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
