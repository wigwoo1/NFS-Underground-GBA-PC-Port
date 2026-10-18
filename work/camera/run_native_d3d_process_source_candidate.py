import runpy,sys
import owned_native_source_process_preparation_candidate as source_process
import live_owned_gpu_worker,owned_world_preparation_service
from live_native_d3d_world_upload_worker_candidate import NativeLiveWorker
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
if __name__=='__main__':
 sys.modules['owned_process_preparation_service']=source_process
 owned_world_preparation_service.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
 live_owned_gpu_worker.LiveOwnedGPUWorker=NativeLiveWorker
 runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
