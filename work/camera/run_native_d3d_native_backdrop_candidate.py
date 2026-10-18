import runpy
import live_owned_gpu_worker,owned_world_preparation_service
from live_native_d3d_native_backdrop_worker_candidate import NativeLiveWorker
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
if __name__=='__main__':
 owned_world_preparation_service.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
 live_owned_gpu_worker.LiveOwnedGPUWorker=NativeLiveWorker
 runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
