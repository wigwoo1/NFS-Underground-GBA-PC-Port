import atexit,json,time,runpy
from pathlib import Path
from owned_spatial_cache_coverage import install,records
install()
def finish():
 p=Path('work/camera/prototype-runs')/('spatial-cache-coverage-'+str(time.time_ns())+'.json')
 p.write_text(json.dumps(dict(columns=['thread_id','hits','misses','fallbacks'],rows=records,scope='Bounded16thread counters; actual cache branch calls, diagnostic overhead; no cadence proof'),indent=2));print(p)
atexit.register(finish)
runpy.run_path('work/camera/run_queued_single_candidate.py',run_name='__main__')
