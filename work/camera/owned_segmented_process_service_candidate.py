"""Isolated spawned child with current segmented reconstruction and owned transport."""
import inspect,textwrap
import owned_source_process_service_candidate as base
from owned_segmented_process_encode_candidate import encode_samples
source=textwrap.dedent(inspect.getsource(base._child))
source=source.replace('def _child(', 'def segmented_child(',1)
source=source.replace(' from owned_prepared_world_motion import PreparedWorldMotion',' from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
source=source.replace(' from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples as PrecomputedWorldSamples',' from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples as PrecomputedWorldSamples')
marker=' from owned_endpoint_road_planner import EndpointRoadPlanner'
source=source.replace(marker,"""
 import owned_scenery_thread_library_install_candidate
 import owned_visibility_thread_library_install_candidate
 import owned_viewport_bounds_fixed_types_install_candidate
 import owned_endpoint_road_planner as planner
 from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
 planner.endpoint_road_span_candidates=endpoint_road_span_candidates
 from owned_endpoint_road_planner import EndpointRoadPlanner""")
namespace=dict(base._child.__globals__);namespace.update(__name__=__name__,encode_samples=encode_samples)
exec(compile(source,'segmented-process-child','exec'),namespace)
segmented_child=namespace['segmented_child']
class ProcessPreparationService(base.ProcessPreparationService):
 def __init__(self,rom,capacity,shared_output=False):
  if shared_output:raise ValueError('Segmented process shared output not qualified')
  if base.os.environ.get('NF_PROCESS_NATIVE_FRAME_JOIN')=='1':raise ValueError('Contiguous child join incompatible with segmented reconstruction')
  self._initialize(rom,capacity,shared_output=False)
source=textwrap.dedent(inspect.getsource(base.ProcessPreparationService.__init__)).replace('def __init__(', 'def _initialize(',1).replace('target=_child','target=segmented_child')
namespace=dict(base.ProcessPreparationService.__init__.__globals__,segmented_child=segmented_child)
exec(compile(source,'segmented-process-service-init','exec'),namespace)
ProcessPreparationService._initialize=namespace['_initialize']

from owned_segmented_frame_candidate import SegmentedFrame
import struct
def retained_frame(prefix,tail,index,owners):
 if type(prefix) is not bytes or len(prefix)<40:raise ValueError('Invalid owned process prefix')
 header=prefix[:8]+b'\0\0\0\0'+prefix[12:40]
 key=(index,header)
 if key not in owners:owners[key]=header+tail
 return SegmentedFrame(prefix,owners[key],40)
class SegmentedProcessSamples(base.ProcessSamples):pass
source=textwrap.dedent(inspect.getsource(base.ProcessSamples.__init__))
source=source.replace('  frame_cache={}', '  frame_cache={}')
source=source.replace(' self.history_only=False',' retained_owners={}\n self.history_only=False')
assert source.count('frame=prefix+tails[index]')==1
source=source.replace('frame=prefix+tails[index]','frame=retained_frame(prefix,tails[index],index,retained_owners)')
namespace=dict(base.ProcessSamples.__init__.__globals__,retained_frame=retained_frame)
exec(compile(source,'segmented-parent-direct-decode','exec'),namespace)
SegmentedProcessSamples.__init__=namespace['__init__']
source=textwrap.dedent(inspect.getsource(base.ProcessPreparationService.submit))
source=source.replace('  reuse=self.previous', '  pack_started=time.perf_counter_ns()\n  reuse=self.previous',1)
source=source.replace('  self.connection.send(request)', '  pack_completed=time.perf_counter_ns()\n  self.connection.send(request)\n  request_sent=time.perf_counter_ns()',1)
source=source.replace('  status,payload,elapsed=self.connection.recv()', '  response_ready=time.perf_counter_ns()\n  status,payload,elapsed=self.connection.recv()\n  payload_received=time.perf_counter_ns()',1)
source=source.replace('dict(parent_received_ns=received,', 'dict(input_pack_ns=pack_completed-pack_started,request_send_ns=request_sent-pack_completed,response_wait_ns=response_ready-request_sent,response_receive_ns=payload_received-response_ready,child_trace_receive_ns=received-payload_received,parent_received_ns=received,',1)
namespace=dict(base.ProcessPreparationService.submit.__globals__,ProcessSamples=SegmentedProcessSamples)
exec(compile(source,'segmented-process-parent-submit','exec'),namespace)
ProcessPreparationService.submit=namespace['submit']
