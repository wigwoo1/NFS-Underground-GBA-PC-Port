"""Same source depth-transition classifier in actual spawned request child."""
import types
import owned_fixed_types_process_service_candidate as fixed
from owned_bounded_fixed_types_service_candidate import BoundedProcessService as Base
def request_child(connection,rom,shared_output,request_name):
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants
 batch.SourceFaceDeterminants=SourceFaceDeterminants
 assert batch.prepare_source_models.__globals__['SourceFaceDeterminants'] is SourceFaceDeterminants
 fixed.request_child(connection,rom,shared_output,request_name)
class ProcessPreparationService(Base):pass
original=fixed.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
