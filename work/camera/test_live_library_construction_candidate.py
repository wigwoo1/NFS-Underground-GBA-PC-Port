import runpy,json
from pathlib import Path
import owned_library_construction_counts_candidate as profile
try:runpy.run_path('work/camera/run_native_ordered_tail_candidate.py',run_name='__main__')
finally:
 profile.live=False
 rows=[dict(library=k[0],caller_file=k[1],caller_function=k[2],during_live=k[3],thread=k[4],count=v[0],elapsed_ms=v[1]/1e6) for k,v in profile.counts.items()]
 Path('work/camera/prototype-runs/library-construction-counts-20261009.json').write_text(json.dumps(dict(rows=rows,dropped=profile.dropped,scope='BoundedCDLLwrapperconstructioncounts with immediate caller; elapsedincludesload/scheduling, notallocation totals. liveflag begins firstgamecontrolstep.'),indent=2));print('LIBRARY_CONSTRUCTION_COUNTS',len(rows),profile.dropped)
