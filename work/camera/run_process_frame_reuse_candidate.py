import runpy
from owned_process_preparation_service import ProcessSamples
ProcessSamples.reuse_immutable_frames=True
runpy.run_path('work/camera/run_native_batch_compact_all_diagnostics.py',run_name='__main__')
