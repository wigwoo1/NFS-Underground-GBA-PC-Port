"""Isolated short HUD release experiment; original renderer/game clock."""
import os,runpy
from pathlib import Path
if __name__=='__main__':
 os.environ['NFSUG_HUD_LEASE_RELEASE_KEEP_GIL']='1'
 os.environ['NFSUG_SOURCE_CALLBACK_RETURN_CYCLES']='1'
 import owned_hud_short_release_gil_candidate as candidate
 try:runpy.run_path(str(Path(__file__).with_name('run_native_endpoint_profile_candidate.py')),run_name='__main__')
 finally:print('SHORT_HUD_RELEASE_STATS',candidate.stats,flush=True)
