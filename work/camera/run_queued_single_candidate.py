"""Isolated one-frame queued burst: every sample retained, original deadlines unchanged."""
from pathlib import Path
from install_combined_performance_candidate import install
install()
source=Path('work/camera/run_segmented_wait_profile_candidate.py').read_text().replace('owned-batch-queued-wait-profile-candidate.dll','owned-batch-queued-single-candidate.dll')
exec(compile(source,'single_queued_candidate','exec'))
