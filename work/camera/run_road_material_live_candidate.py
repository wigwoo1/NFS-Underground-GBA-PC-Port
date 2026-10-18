"""Isolated road material reuse in aggregate segmented singlecommit live pipeline."""
import runpy
from owned_road_material_resolution_candidate import install
install()
runpy.run_path('work/camera/run_queued_single_candidate.py',run_name='__main__')
