import runpy
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_native_batch_candidate import NativeBatchWorker
NativeBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
runpy.run_path('work/camera/run_native_batch_compact_diagnostics.py',run_name='__main__')
