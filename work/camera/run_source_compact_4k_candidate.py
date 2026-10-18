"""Single queued playable source renderer with isolated 4K output window."""
from pathlib import Path
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_source_batch_candidate import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
source=Path('work/camera/run_queued_source_anchor_candidate.py').read_text()
assert source.count('owned-batch-queued-candidate.dll')==1
assert source.count('owned-sky-source-context-candidate.dll')==1
source=source.replace('owned-batch-queued-candidate.dll','owned-batch-queued-single-candidate.dll').replace('owned-sky-source-context-candidate.dll','owned-sky-source-context-4k-candidate.dll')
exec(compile(source,'4k_single_playable_candidate','exec'))
