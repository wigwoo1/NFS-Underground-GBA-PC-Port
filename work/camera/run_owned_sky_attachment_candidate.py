"""Isolated producer sky attachment borrows already-owned exact frame bytes."""
import runpy
from pathlib import Path
original_run=runpy.run_path
TARGET='work/camera/run_owned_native_prototype.py'
def run(path,*args,**kwargs):
 if str(path).replace('\\','/')!=TARGET:return original_run(path,*args,**kwargs)
 source=Path(path).read_text()
 needle='sky_frame=attach_sky(C.string_at(frame,size.value),scene)'
 assert source.count(needle)==1
 source=source.replace(needle,'sky_frame=attach_sky(adapted if adapted is not None else C.string_at(frame,size.value),scene)')
 scope=dict(__name__='__main__',__file__=str(Path(path).resolve()))
 exec(compile(source,str(path),'exec'),scope)
 return scope
runpy.run_path=run
original_run('work/camera/run_road_material_live_candidate.py',run_name='__main__')
