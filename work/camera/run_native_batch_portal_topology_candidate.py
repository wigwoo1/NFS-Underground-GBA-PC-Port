import runpy
from owned_motion_visibility import PortalMotionPair
PortalMotionPair.cache_topology=True
runpy.run_path('work/camera/run_native_batch_compact_all_diagnostics.py',run_name='__main__')
