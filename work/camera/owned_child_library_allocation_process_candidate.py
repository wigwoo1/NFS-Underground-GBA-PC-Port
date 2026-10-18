"""Count actual child native wrapper construction without changing ownership."""
import types
import owned_fixed_types_process_service_candidate as fixed
from owned_bounded_fixed_types_service_candidate import BoundedProcessService as Base
def request_child(connection,rom,shared_output,request_name):
 import ctypes as C,time,json,os,collections,sys
 from pathlib import Path
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants
 batch.SourceFaceDeterminants=SourceFaceDeterminants
 original=C.CDLL;counts=collections.Counter();sites=collections.Counter()
 def tracked(name,*args,**kwargs):
  frame=sys._getframe(1);site=(Path(frame.f_code.co_filename).name,frame.f_code.co_name)
  counts[Path(str(name)).name]+=1;sites[site]+=1
  return original(name,*args,**kwargs)
 C.CDLL=tracked
 try:fixed.request_child(connection,rom,shared_output,request_name)
 finally:
  C.CDLL=original
  Path('work/camera/prototype-runs/child-library-allocations-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),counts=dict(counts),sites=[dict(file=k[0],function=k[1],count=v) for k,v in sites.items()],scope='Actual wrapper constructor counts/sites, same returned native wrappers; diagnostic not cadence qualification.'),indent=2))
class ProcessPreparationService(Base):pass
original=fixed.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
