"""Isolated fully validated sky-byte identity reuse in live producer."""
import runpy
from owned_sky_attached_reuse_candidate import install
install()
runpy.run_path('work/camera/run_owned_sky_attachment_candidate.py',run_name='__main__')
