"""DXGI fullscene candidate with current compact diagnostics and exact process transport."""
import runpy,sys
from live_native_batch_candidate import NativeBatchWorker
from owned_compact_diagnostics import CompactPresentationDiagnostics
from owned_process_preparation_service import ProcessSamples
NativeBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
ProcessSamples.reuse_immutable_frames=True
if '--shared-output-dedup' not in sys.argv:sys.argv.append('--shared-output-dedup')
runpy.run_path('work/camera/run_dxgi_phase_candidate.py',run_name='__main__')
