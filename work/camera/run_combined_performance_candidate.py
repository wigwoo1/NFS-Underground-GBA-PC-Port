import runpy
from install_combined_performance_candidate import install
install()
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
