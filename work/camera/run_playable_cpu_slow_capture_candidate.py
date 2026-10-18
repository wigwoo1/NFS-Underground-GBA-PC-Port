"""Bounded retained actual-playable heavy HUD inputs; save after shutdown."""
import runpy
from live_source_batch_candidate import SourceBatchWorker
SourceBatchWorker.slow_hud_capture_ns=5_000_000
runpy.run_path('work/camera/run_playable_cpu_profile_candidate.py',run_name='__main__')
