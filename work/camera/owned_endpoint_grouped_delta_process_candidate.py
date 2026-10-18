"""Isolated grouped endpoint cache in parent and actual preparation child."""
import types
import owned_child_road_wrapper_reuse_process_candidate as base
def install():
 import owned_endpoint_grouped_delta_candidate as grouped
 import owned_portal_traversal as traversal
 traversal.endpoint_delta=grouped.endpoint_delta
 assert traversal.endpoint_delta is grouped.endpoint_delta
install()
def request_child(*args):
 install()
 base.request_child(*args)
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
