import runpy
import live_owned_gpu_worker
from live_native_batch_candidate import NativeBatchWorker
if __name__=='__main__':
 live_owned_gpu_worker.LiveOwnedGPUWorker=NativeBatchWorker
 runpy.run_path('work/camera/run_owned_capture_padding_candidate.py',run_name='__main__')
