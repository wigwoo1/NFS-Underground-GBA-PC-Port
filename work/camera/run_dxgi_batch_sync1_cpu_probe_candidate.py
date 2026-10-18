import runpy
import live_owned_gpu_worker
from live_native_batch_cpu_probe_candidate import NativeBatchWorker
NativeBatchWorker.dxgi_enabled=True
NativeBatchWorker.dxgi_bridge_name='owned-dx-present-sync1-frame-stats-cpu-bridge.dll'
live_owned_gpu_worker.LiveOwnedGPUWorker=NativeBatchWorker
runpy.run_path('work/camera/run_owned_native_prototype.py',run_name='__main__')
