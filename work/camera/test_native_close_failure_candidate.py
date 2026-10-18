"""Injected base-close failure must survive bounded report serialization."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import run_native_d3d_bounded_diagnostics_candidate as runner
from owned_recent_rows_candidate import RecentRows
from owned_pause_window_candidate import PauseWindow
from owned_recent_mutable_timings_candidate import RecentMutableTimingRows
from owned_validated_bounded_diagnostics_candidate import ValidatedPresentationDiagnostics
failure=RuntimeError('injected close failure');checks=[]
s=runner.BoundedService.__new__(runner.BoundedService);s.stage_samples=RecentRows();s.stage_samples.append(dict(stage='completed'));s.pipeline=SimpleNamespace(timings=RecentMutableTimingRows());s.pipeline.timings.append(dict(status='failed',finalized_ns=123))
with patch.object(runner.process_module.ProcessPreparationService,'close',side_effect=failure):
 try:s.close()
 except RuntimeError as error:assert error is failure
 else:raise AssertionError('Failure swallowed')
assert isinstance(s.stage_samples,list) and isinstance(s.pipeline.timings,list)
json.dumps(dict(stages=s.stage_samples,queue=s.pipeline.timings,retention=s.preparation_retention));checks.append('service')
w=runner.BoundedWorker.__new__(runner.BoundedWorker);w.pause_events=PauseWindow();w.world_resets=RecentRows();w.results=ValidatedPresentationDiagnostics(1,0);w.boundary_stage_samples=RecentRows();w.submit_stage_samples=RecentRows();w.boundary_stage_samples.append(dict(stage='boundary'));w.submit_stage_samples.append(dict(stage='submit'))
with patch.object(runner.Base,'close',side_effect=failure):
 try:w.close()
 except RuntimeError as error:assert error is failure
 else:raise AssertionError('Failure swallowed')
assert isinstance(w.results,list) and isinstance(w.boundary_stage_samples,list) and isinstance(w.submit_stage_samples,list)
json.dumps(dict(results=w.results,boundary=w.boundary_stage_samples,submit=w.submit_stage_samples));checks.append('worker')
out=dict(result='PASS_CLOSE_FAILURE_SERIALIZATION',checks=checks,scope='Injected base-close error propagation and diagnostic conversion only; does not prove native resources close after a real failure.')
Path('work/camera/prototype-runs/native-close-failure-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
