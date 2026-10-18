import runpy
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.slow_hud_capture_ns=5_000_000
runpy.run_path('work/camera/run_native_batch_compact_all_diagnostics.py',run_name='__main__')
