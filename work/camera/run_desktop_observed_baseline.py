"""Record actual renderer process desktop before visible presentation test."""
import runpy,sys,time
from pathlib import Path
original_args=sys.argv[:]
output=Path('work/camera/prototype-runs')/('renderer-desktop-'+str(time.time_ns())+'.json')
sys.argv=['work/camera/check_presentation_desktop.py',str(output)]
try:runpy.run_path(sys.argv[0],run_name='__main__')
finally:sys.argv=original_args
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
