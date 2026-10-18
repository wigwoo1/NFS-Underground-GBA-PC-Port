"""Isolated private native pose-array copies with validated sky-byte reuse."""
import runpy
from owned_source_array_copy_candidate import install
install()
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
