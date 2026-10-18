import runpy
import owned_closed_viewport as original
from owned_closed_viewport_cache_candidate import ClosedViewport
original.ClosedViewport=ClosedViewport
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
