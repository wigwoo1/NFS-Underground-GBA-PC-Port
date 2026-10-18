"""Isolated exact traversal selection for parent and preparation child."""
import types
import owned_child_road_wrapper_reuse_process_candidate as base
def install():
 import owned_motion_visibility as motion
 import owned_wall_region_candidates as endpoint
 from owned_portal_point_reuse_candidate import traverse
 motion.traverse=endpoint.traverse=traverse
 assert motion.traverse is endpoint.traverse is traverse
install()
def request_child(*args):
 install()
 base.request_child(*args)
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
