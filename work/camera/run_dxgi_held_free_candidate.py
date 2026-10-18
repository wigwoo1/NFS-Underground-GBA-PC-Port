import runpy
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.held_frame_free_enabled=True
runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
