"""Isolated geometry-buffer reuse with validated sky-byte reuse and baseline GPU."""
import runpy,sys
from pathlib import Path
original_read=Path.read_text
target=Path('work/camera/run_owned_native_prototype.py').resolve()
def read(path,*args,**kwargs):
 source=original_read(path,*args,**kwargs)
 if path.resolve()==target:
  assert 'viewport-sky-capture-probe.dll' in source
  source=source.replace('viewport-sky-capture-probe.dll','viewport-sky-geometry-reuse-probe.dll')
 return source
Path.read_text=read
sys.argv=[x.replace('viewport-sky-capture-probe.dll','viewport-sky-geometry-reuse-probe.dll') for x in sys.argv]
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
