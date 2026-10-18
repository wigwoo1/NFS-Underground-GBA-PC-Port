"""Spatial sky with one-frame ordered draw/commit; isolated candidate."""
from pathlib import Path
p=Path('work/camera/run_source_spatial_sky_candidate.py')
s=p.read_text(); old="'owned-batch-queued-candidate.dll'"
assert s.count(old)==1
exec(compile(s.replace(old,"'owned-batch-queued-single-candidate.dll'"),str(p),'exec'),globals())
