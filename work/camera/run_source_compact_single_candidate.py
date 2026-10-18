"""Playable compact diagnostics with one queued frame before each commit."""
from pathlib import Path
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_source_batch_candidate import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
source=Path('work/camera/run_queued_source_anchor_candidate.py').read_text()
assert source.count('owned-batch-queued-candidate.dll')==1
source=source.replace('owned-batch-queued-candidate.dll','owned-batch-queued-single-candidate.dll')
exec(compile(source,'single_ordered_playable_candidate','exec'))
