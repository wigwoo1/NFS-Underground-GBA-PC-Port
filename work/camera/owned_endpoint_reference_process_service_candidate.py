"""Isolated validated endpoint references with copied geometry and source sidecar."""
import inspect,textwrap,types
import owned_endpoint_tail_process_service_candidate as endpoint
import owned_wall_record_reuse_process_service_candidate as wall
import owned_segmented_shared_process_service_candidate as shared
import owned_shared_request_service_candidate as request
import owned_source_process_service_candidate as base
from owned_endpoint_tail_reference_candidate import encode_samples,resolve_frame

def reference_frame(prefix,tail,index,owners):
 if type(tail)is tuple:return resolve_frame(prefix,tail,owners['endpoints'])
 return endpoint.endpoint_frame(prefix,tail,index,owners)
class ReferenceSamples(endpoint.EndpointSamples):pass
source=textwrap.dedent(inspect.getsource(base.ProcessSamples.__init__))
source=source.replace('def __init__(self,encoded,identity):','def __init__(self,encoded,identity,endpoints):')
source=source.replace(' self.history_only=False'," if type(endpoints)is not tuple or len(endpoints)!=2 or any(type(x)is not bytes or len(x)<40 for x in endpoints):raise ValueError('Invalid original endpoints')\n retained_owners={'endpoints':endpoints}\n self.endpoint_base_reuses=0\n self.history_only=False")
source=source.replace('any(not isinstance(t,bytes) for t in tails)','any(type(t) not in (bytes,tuple) for t in tails)')
source=source.replace('not isinstance(index,int)','type(index)is not int')
source=source.replace('frame=prefix+tails[index]','frame=reference_frame(prefix,tails[index],index,retained_owners)')
source=source.replace('from owned_source_process_sidecar_candidate import decode as decode_source','from owned_source_extent_sidecar_candidate import decode as decode_source')
source=source.replace('  self.samples[alpha]=(frame,*arrays,detail)','  self.samples[alpha]=(frame,*arrays,detail)\n  self.endpoint_base_reuses+=any(frame.base is x for x in endpoints)')
namespace=dict(base.ProcessSamples.__init__.__globals__,reference_frame=reference_frame)
exec(compile(source,'reference-parent-decode','exec'),namespace);ReferenceSamples.__init__=namespace['__init__']
builder=dict(shared.__dict__)
exec(shared.__file__ and __import__('pathlib').Path(shared.__file__).read_text().split('from owned_segmented_borrowed_tail_encode_candidate')[0],builder)
source=builder['source'].replace('def shared_segmented_child(', 'def reference_child(',1)
old='encode_samples(samples.samples,encode_trace,borrow_tails=shared_memory is not None)';assert source.count(old)==1
source=source.replace(old,'encode_samples(samples.samples,(a,b),encode_trace)')
namespace=dict(shared.shared_segmented_child.__globals__,__name__=__name__,encode_samples=encode_samples)
exec(compile(source,'reference-child','exec'),namespace);reference_child=namespace['reference_child']

def request_child(connection,rom,shared_output,request_name):
 import owned_wall_record_reuse_install_candidate
 wrapped=request.ChildConnection(connection,request_name)
 try:reference_child(wrapped,rom,shared_output)
 finally:wrapped.close()
class ProcessPreparationService(wall.ProcessPreparationService):pass
original=request.ProcessPreparationService._initialize_request
namespace=dict(original.__globals__,request_child=request_child)
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
namespace=dict(endpoint.ProcessPreparationService.submit.__globals__,ProcessSamples=ReferenceSamples)
exec(compile(endpoint.source,'reference-parent-submit','exec'),namespace);ProcessPreparationService.submit=namespace['submit']
