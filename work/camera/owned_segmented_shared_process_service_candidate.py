"""Isolated copied shared output; acknowledgement precedes mapping reuse."""
import inspect,textwrap
import owned_segmented_process_service_candidate as segmented
import owned_source_process_service_candidate as base
source=textwrap.dedent(inspect.getsource(base._child)).replace('def _child(', 'def shared_segmented_child(',1)
source=source.replace(' from owned_prepared_world_motion import PreparedWorldMotion',' from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
source=source.replace(' from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples as PrecomputedWorldSamples',' from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples as PrecomputedWorldSamples')
source=source.replace(' from owned_endpoint_road_planner import EndpointRoadPlanner',"""
 import owned_scenery_thread_library_install_candidate
 import owned_visibility_thread_library_install_candidate
 import owned_viewport_bounds_fixed_types_install_candidate
 import owned_endpoint_road_planner as planner
 from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
 planner.endpoint_road_span_candidates=endpoint_road_span_candidates
 from owned_endpoint_road_planner import EndpointRoadPlanner""")
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as borrowed_encode
namespace=dict(base._child.__globals__,__name__=__name__,encode_samples=borrowed_encode)
exec(compile(source,'shared-segmented-child','exec'),namespace)
shared_segmented_child=namespace['shared_segmented_child']
class ProcessPreparationService(segmented.ProcessPreparationService):
 def __init__(self,rom,capacity,shared_output=True):
  if not shared_output:raise ValueError('Shared candidate requires owned output mapping')
  if base.os.environ.get('NF_PROCESS_NATIVE_FRAME_JOIN')=='1':raise ValueError('Contiguous join incompatible')
  self._initialize_shared(rom,capacity,True)
source=textwrap.dedent(inspect.getsource(base.ProcessPreparationService.__init__)).replace('def __init__(', 'def _initialize_shared(',1).replace('target=_child','target=shared_segmented_child')
namespace=dict(base.ProcessPreparationService.__init__.__globals__,shared_segmented_child=shared_segmented_child)
exec(compile(source,'shared-segmented-init','exec'),namespace)
ProcessPreparationService._initialize_shared=namespace['_initialize_shared']

class ExtentProcessSamples(segmented.SegmentedProcessSamples):pass
source=textwrap.dedent(inspect.getsource(base.ProcessSamples.__init__))
source=source.replace(' self.history_only=False',' retained_owners={}\n self.history_only=False')
source=source.replace('frame=prefix+tails[index]','frame=retained_frame(prefix,tails[index],index,retained_owners)')
source=source.replace('from owned_source_process_sidecar_candidate import decode as decode_source','from owned_source_extent_sidecar_candidate import decode as decode_source')
namespace=dict(base.ProcessSamples.__init__.__globals__,retained_frame=segmented.retained_frame)
exec(compile(source,'shared-parent-extent-decode','exec'),namespace)
ExtentProcessSamples.__init__=namespace['__init__']
namespace=dict(segmented.ProcessPreparationService.submit.__globals__,ProcessSamples=ExtentProcessSamples)
exec(compile(segmented.source,'shared-parent-extent-submit','exec'),namespace)
ProcessPreparationService.submit=namespace['submit']
