"""Isolated aggregate candidates with owned segmented frames; stable launcher untouched."""
import runpy
from install_combined_performance_candidate import install
install()
runpy.run_path('work/camera/run_segmented_wait_profile_candidate.py',run_name='__main__')
