"""Validated optimized preparation with isolated segmented 4K window GPU."""
import runpy
from pathlib import Path
original_read=Path.read_text
target=Path('work/camera/run_segmented_wait_profile_candidate.py').resolve()
def read(path,*args,**kwargs):
 source=original_read(path,*args,**kwargs)
 if path.resolve()==target:
  assert source.count('owned-gpu-segmented-source-candidate.dll')==1
  source=source.replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-4k-candidate.dll')
 return source
Path.read_text=read
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
