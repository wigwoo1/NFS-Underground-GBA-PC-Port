"""Apply existing parent road candidate implementation in actual child."""
import types
import owned_depth_transition_process_service_candidate as depth
def request_child(*args):
 import owned_endpoint_road_planner as planner
 from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
 planner.endpoint_road_span_candidates=endpoint_road_span_candidates
 depth.request_child(*args)
class ProcessPreparationService(depth.ProcessPreparationService):pass
original=depth.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
