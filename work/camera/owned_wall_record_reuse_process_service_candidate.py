"""Isolated parent and child wall record reuse, original transport/lifetime."""
import types
import owned_endpoint_tail_process_service_candidate as endpoint
import owned_shared_request_service_candidate as request

def request_child(connection,rom,shared_output,request_name):
 import owned_wall_record_reuse_install_candidate
 return request.request_child(connection,rom,shared_output,request_name)
class ProcessPreparationService(endpoint.ProcessPreparationService):pass
original=request.ProcessPreparationService._initialize_request
namespace=dict(original.__globals__,request_child=request_child)
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
