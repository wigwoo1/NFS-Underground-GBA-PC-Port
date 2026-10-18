import runpy
import live_owned_gpu_worker
from live_advancement_batch_candidate import AdvancementBatchWorker
live_owned_gpu_worker.LiveOwnedGPUWorker=AdvancementBatchWorker
runpy.run_path("work/camera/run_owned_native_prototype.py",run_name="__main__")
