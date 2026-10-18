"""Spatial sky/single commit with existing isolated preparation optimizations."""
from install_combined_performance_candidate import install
install()
import runpy
runpy.run_path('work/camera/run_spatial_sky_single_candidate.py',run_name='__main__')
