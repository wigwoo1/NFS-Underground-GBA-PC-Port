"""Lossless completed diagnostic records; no GC policy or game timing changes."""
import runpy,sys
import live_owned_gpu_worker,owned_world_preparation_service
import owned_native_source_process_preparation_candidate as process_module
from owned_compact_diagnostics import CompactDiagnostics,CompactPresentationDiagnostics
from live_native_d3d_hud_profile_worker_candidate import NativeLiveWorker as Base
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
class CompactService(process_module.ProcessPreparationService):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.stage_samples=CompactDiagnostics()
 def close(self):
  super().close();self.compact_diagnostic_stats=self.stage_samples.stats();self.stage_samples=self.stage_samples.snapshot()
class CompactWorker(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.results=CompactPresentationDiagnostics()
 def close(self):
  super().close();self.compact_presentation_diagnostic_stats=self.results.stats();self.results=self.results.snapshot()
if __name__=='__main__':
 process_module.ProcessPreparationService=CompactService
 sys.modules['owned_process_preparation_service']=process_module
 owned_world_preparation_service.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
 live_owned_gpu_worker.LiveOwnedGPUWorker=CompactWorker
 runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
