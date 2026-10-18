"""Fresh later-interval selected target diagnostic; no default changes."""
import types,sys,runpy
from pathlib import Path
name='live_source_sky_pixels_candidate'; m=types.ModuleType(name)
m.__file__=str(Path('work/camera/live_source_sky_pixels_candidate.py').resolve())
s=Path(m.__file__).read_text()
assert "['display_index']>=180" in s
s=s.replace("['display_index']>=180", "['display_index']>=400").replace('work/camera/live-sky-selected-later.png','work/camera/live-sky-selected-fresh-400.png')
exec(compile(s,m.__file__,'exec'),m.__dict__);sys.modules[name]=m
runpy.run_path('work/camera/run_source_sky_pixels_candidate.py',run_name='__main__')
