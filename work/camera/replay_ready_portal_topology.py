"""Isolated existing portal topology cache on exact captured preparation replay."""
import runpy
from owned_motion_visibility import PortalMotionPair
PortalMotionPair.cache_topology=True
runpy.run_path('work/camera/replay_captured_preparation_ready.py',run_name='__main__')
