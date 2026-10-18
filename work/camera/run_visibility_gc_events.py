"""Observe actual collections alongside lightweight visibility; GC policy unchanged."""
import gc,atexit,json,runpy,time
from pathlib import Path
from owned_gc_trace import CollectionTrace
before=list(gc.callbacks);enabled=gc.isenabled();thresholds=gc.get_threshold();trace=CollectionTrace()
def save():
 trace.close();assert gc.callbacks==before and gc.isenabled()==enabled and gc.get_threshold()==thresholds
 p=Path('work/camera/prototype-runs')/('visibility-gc-events-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(collections=trace.rows,dropped=trace.dropped,policy_unchanged=True,scope='Bounded real collection events with owner thread; diagnostic overhead and overlaps are not exclusive causal attribution.'),indent=2));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_visibility_light_candidate.py',run_name='__main__')
