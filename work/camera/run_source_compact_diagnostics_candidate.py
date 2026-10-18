"""Separate source renderer with lossless compact retained diagnostic storage."""
import runpy
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_source_batch_candidate import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
runpy.run_path('work/camera/run_queued_source_anchor_candidate.py',run_name='__main__')
