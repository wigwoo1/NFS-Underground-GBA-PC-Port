import atexit,json,time,runpy,sys
from pathlib import Path
from owned_spatial_cache_coverage import install,records
install()
def finish():
 bindings=[]
 for name,module in list(sys.modules.items()):
  if module is None:continue
  cls=vars(module).get('SpatialDescriptors')
  if isinstance(cls,type):bindings.append(dict(module=name,class_id=id(cls),class_module=cls.__module__,init_module=cls.__init__.__module__,init_file=cls.__init__.__code__.co_filename))
 p=Path('work/camera/prototype-runs')/('spatial-cache-coverage-'+str(time.time_ns())+'.json')
 p.write_text(json.dumps(dict(bindings=bindings,columns=['thread_id','hits','misses','fallbacks'],rows=records,scope='Bounded16thread counters; actual cache branch calls, diagnostic overhead; no cadence proof'),indent=2));print(p)
atexit.register(finish)
runpy.run_path('work/camera/run_queued_single_candidate.py',run_name='__main__')
