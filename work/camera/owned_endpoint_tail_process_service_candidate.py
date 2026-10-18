"""Reuse original immutable endpoints only after exact tail validation."""
import inspect,textwrap,struct
import owned_shared_request_service_candidate as request
import owned_segmented_shared_process_service_candidate as shared
import owned_segmented_process_service_candidate as segmented
import owned_source_process_service_candidate as base
from owned_segmented_frame_candidate import SegmentedFrame
from owned_immutable_tail_equal_candidate import equal as exact_tail_equal

def endpoint_frame(prefix,tail,index,owners):
 h=struct.unpack_from('<6I2Q',prefix);key=(index,prefix[:8]+b'\0\0\0\0'+prefix[12:40])
 if key in owners:
  endpoint,offset=owners[key];return SegmentedFrame(prefix,endpoint,offset)
 for endpoint in owners['endpoints']:
  b=struct.unpack_from('<6I2Q',endpoint);offset=40+b[2]
  if b[0]==h[0] and b[1]==h[1] and b[3:]==h[3:] and offset<=len(endpoint) and len(endpoint)-offset==len(tail) and exact_tail_equal(endpoint,offset,tail):
   value=SegmentedFrame(prefix,endpoint,offset);owners[key]=(endpoint,offset);return value
 # Unmatched bytes remain independently owned; never bind a merely similar HUD.
 value=segmented.retained_frame(prefix,tail,index,{})
 owners[key]=(value.base,value.tail_offset);return value
class EndpointSamples(shared.ExtentProcessSamples):pass
source=textwrap.dedent(inspect.getsource(base.ProcessSamples.__init__))
source=source.replace('def __init__(self,encoded,identity):','def __init__(self,encoded,identity,endpoints):')
source=source.replace(' self.history_only=False'," if type(endpoints)is not tuple or len(endpoints)!=2 or any(type(x)is not bytes or len(x)<40 for x in endpoints):raise ValueError('Invalid original endpoints')\n retained_owners={'endpoints':endpoints}\n self.endpoint_base_reuses=0\n self.history_only=False")
source=source.replace('frame=prefix+tails[index]','frame=endpoint_frame(prefix,tails[index],index,retained_owners)')
source=source.replace('from owned_source_process_sidecar_candidate import decode as decode_source','from owned_source_extent_sidecar_candidate import decode as decode_source')
source=source.replace('  self.samples[alpha]=(frame,*arrays,detail)','  self.samples[alpha]=(frame,*arrays,detail)\n  self.endpoint_base_reuses+=any(frame.base is endpoint for endpoint in endpoints)')
namespace=dict(base.ProcessSamples.__init__.__globals__,endpoint_frame=endpoint_frame)
exec(compile(source,'endpoint-source-parent-decode','exec'),namespace);EndpointSamples.__init__=namespace['__init__']
class ProcessPreparationService(request.ProcessPreparationService):pass
source=segmented.source
source=source.replace('result=ProcessSamples(payload,(older[1].graph.epoch,older[1].graph.refresh,newer[1].graph.refresh))','result=ProcessSamples(payload,(older[1].graph.epoch,older[1].graph.refresh,newer[1].graph.refresh),(older[0],newer[0]))')
source=source.replace('dict(input_pack_ns=','dict(endpoint_base_reuses=result.endpoint_base_reuses,input_pack_ns=')
namespace=dict(shared.ProcessPreparationService.submit.__globals__,ProcessSamples=EndpointSamples)
exec(compile(source,'endpoint-source-parent-submit','exec'),namespace);ProcessPreparationService.submit=namespace['submit']
