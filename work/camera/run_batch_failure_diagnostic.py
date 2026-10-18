"""Intentional diagnostic failure; never used by playable launchers."""
import runpy
from live_native_batch_candidate import NativeBatchWorker
def fail(self,*args,**kwargs):raise RuntimeError('NF_DIAGNOSTIC_BATCH_FAILURE')
NativeBatchWorker._draw_intervals=fail
runpy.run_path('work/camera/run_process_transport_dedup_candidate.py',run_name='__main__')
