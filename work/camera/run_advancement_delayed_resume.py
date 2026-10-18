import runpy
from live_advancement_batch_candidate import AdvancementBatchWorker
AdvancementBatchWorker.diagnostic_resume_delay_seconds=.075
runpy.run_path("work/camera/run_advancement_batch_candidate.py",run_name="__main__")
