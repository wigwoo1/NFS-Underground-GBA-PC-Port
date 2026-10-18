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
from live_segmented_source_batch import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
import runpy,json,time
from pathlib import Path
import live_native_batch_candidate as original
from live_segmented_source_batch import SourceBatchWorker as NativeBatchWorker
original.NativeBatchWorker=NativeBatchWorker
import owned_world_preparation_service as preparation
from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples
preparation.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
NativeBatchWorker.batch_bridge_name='owned-batch-present-candidate.dll'
NativeBatchWorker.dxgi_enabled=True
NativeBatchWorker.dxgi_bridge_name='owned-dx-source-diagnostic-bridge.dll'
NativeBatchWorker.gpu_ready_enabled=False
NativeBatchWorker.gpu_queued_enabled=False
NativeBatchWorker.queued_ordered_gpu=False
NativeBatchWorker.queued_draw_probe_enabled=False
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
original_before_gpu_close=NativeBatchWorker._before_gpu_close
def verified_before_gpu_close(self):
 import ctypes as C
 gpu=C.CDLL(str(self.p/NativeBatchWorker.gpu_renderer_name))
 gpu.nf_segmented_draw_trace_read.argtypes=[C.c_uint,C.c_void_p];draw_rows=[]
 for index in range(gpu.nf_segmented_draw_trace_count()):
  row=(C.c_uint64*18)();assert gpu.nf_segmented_draw_trace_read(index,row)==0;draw_rows.append(list(row))
 dropped=gpu.nf_segmented_draw_trace_dropped()
 draw_path=Path('work/camera/prototype-runs')/('segmented-draw-stages-'+str(time.time_ns())+'.json')
 draw_path.write_text(json.dumps(dict(rows=draw_rows,dropped=dropped,stages=['sky','geometry','HUD'],scope='Callback wall/CPU-cycle boundaries and stage boundaries; no physical scanout certification.'),indent=2));print(draw_path)
 original_before_gpu_close(self)
 self.dxgi_shutdown['source_draw_trace']=str(draw_path)
 stats=(C.c_uint64*4)();self.dxgi_bridge.nf_dx_window_stats.argtypes=[C.c_void_p]
 assert self.dxgi_bridge.nf_dx_window_stats(stats)==0 and stats[0]==stats[1] and stats[3]==0
 self.dxgi_shutdown['window_stats']=list(stats)
 self.dxgi_bridge.nf_dx_phase_read.argtypes=[C.c_uint,C.c_void_p];rows=[]
 for index in range(self.dxgi_bridge.nf_dx_phase_count()):
  row=(C.c_uint64*18)();assert self.dxgi_bridge.nf_dx_phase_read(index,row)==0;rows.append(list(row))
 path=Path('work/camera/prototype-runs')/('source-dxgi-stages-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(rows=rows,phases=['setup_and_get_buffer','interop_lock','gl_blit','interop_unlock','resource_copy','present','restore_cleanup'],scope='Native callback ordered boundary timestamps and execution cycles; waits and scheduler time included, not exclusive driver/GPU causality.'),indent=2));print(path)
 self.dxgi_shutdown['phase_trace']=str(path)
NativeBatchWorker._before_gpu_close=verified_before_gpu_close
original_draw_intervals=NativeBatchWorker._draw_intervals
def diagnostic_draw_intervals(self,*args,**kwargs):
 import ctypes as C
 if not getattr(self,'source_draw_trace_initialized',False):
  gpu=args[0];assert gpu.nf_segmented_draw_trace_reset()==0;self.source_draw_trace_initialized=True
 try:return original_draw_intervals(self,*args,**kwargs)
 except BaseException as error:
  tb=error.__traceback__;evidence=[]
  while tb is not None:
   owned=tb.tb_frame.f_locals.get('owned')
   if owned is not None and hasattr(owned,'presents'):
    evidence.append(dict(function=tb.tb_frame.f_code.co_name,presents=[dict(result=x.result,elapsed_ns=x.elapsed_ns) for x in owned.presents],source_draws=[dict(result=x.context.draw.result,started_ns=x.context.draw.started_ns,completed_ns=x.context.draw.completed_ns) for x in getattr(owned,'source_draws',[])]))
   tb=tb.tb_next
  path=Path('work/camera/prototype-runs')/('source-dxgi-failure-'+str(time.time_ns())+'.json');diagnostic=(C.c_uint64*5)();self.dxgi_bridge.nf_dx_creation_diagnostic.argtypes=[C.c_void_p];status=self.dxgi_bridge.nf_dx_creation_diagnostic(diagnostic);path.write_text(json.dumps(dict(error=repr(error),contexts=evidence,creation_diagnostic=list(diagnostic),diagnostic_result=status),indent=2));print(path)
  raise
NativeBatchWorker._draw_intervals=diagnostic_draw_intervals
runpy.run_path('work/camera/run_native_capture_padding_batch.py',run_name='__main__')


