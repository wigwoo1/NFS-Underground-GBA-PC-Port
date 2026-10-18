import owned_sampled_world_frame as assembly
from owned_segmented_frame_candidate import SegmentedFrame
import threading
_segmented_trace=threading.local()
def segmented_join(header,geometry,base,offset):
 value=SegmentedFrame.join(header,geometry,base,offset)
 _segmented_trace.last=dict(segmented=True,prefix_bytes=len(value.prefix),retained_base_bytes=len(base),retained_tail_bytes=len(value.tail),materialized=False)
 return value
assembly.join_frame=segmented_join
assembly.join_frame_trace=lambda:getattr(_segmented_trace,'last',None)
"""Isolated complete source/HUD/spatial sky DXGI presentation comparison."""
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_segmented_wait_profile_candidate import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
import runpy,json,time
from pathlib import Path
import live_native_batch_candidate as original
from live_segmented_wait_profile_candidate import SourceBatchWorker as NativeBatchWorker
original.NativeBatchWorker=NativeBatchWorker
import owned_world_preparation_service as preparation
from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples
preparation.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
NativeBatchWorker.batch_bridge_name='owned-batch-queued-wait-profile-candidate.dll'
NativeBatchWorker.dxgi_enabled=False
NativeBatchWorker.dxgi_bridge_name='owned-dx-source-diagnostic-bridge.dll'
NativeBatchWorker.gpu_ready_enabled=False
NativeBatchWorker.gpu_queued_enabled=True
NativeBatchWorker.queued_ordered_gpu=True
NativeBatchWorker.queued_draw_probe_enabled=True
NativeBatchWorker.ready_adapter_name='owned-gpu-ready-bounded-candidate.dll'
NativeBatchWorker.gpu_renderer_name='owned-gpu-segmented-source-candidate.dll'
def after_close(self,gpu):
 import ctypes as C
 gpu.nf_owned_gpu_pool_stats.argtypes=[C.c_void_p];gpu.nf_owned_gpu_pool_fences.argtypes=[C.c_void_p]
 targets=(C.c_uint64*5)();fences=(C.c_uint64*4)()
 assert gpu.nf_owned_gpu_pool_stats(targets)==0 and list(targets)==[0]*5
 assert gpu.nf_owned_gpu_pool_fences(fences)==0 and fences[0]==fences[1] and fences[3]==0
 path=Path('work/camera/prototype-runs')/('pool-cleanup-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(targets=list(targets),fences=list(fences)),indent=2));print(path)
NativeBatchWorker._after_gpu_close=after_close
runpy.run_path('work/camera/run_native_batch_candidate.py',run_name='__main__')
