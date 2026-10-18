import runpy
from pathlib import Path
original=Path.read_text;target=Path('work/camera/run_queued_source_anchor_candidate.py').resolve()
def read(path,*args,**kwargs):
 source=original(path,*args,**kwargs)
 if path.resolve()==target:
  assert source.count('owned-sky-source-context-candidate.dll')==1
  source=source.replace('owned-sky-source-context-candidate.dll','owned-gpu-playable-row-view-candidate.dll')
 return source
Path.read_text=read
runpy.run_path('work/camera/run_source_compact_single_candidate.py',run_name='__main__')
