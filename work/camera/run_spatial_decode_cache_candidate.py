"""Isolated spatial decode cache with complete segmented one-frame renderer."""
import runpy
from owned_spatial_decode_cache_candidate import install
install()
runpy.run_path('work/camera/run_queued_single_candidate.py',run_name='__main__')
