"""Two boundary inventories; no per-frame or GC callback enumeration."""
import gc,time,collections,json,runpy,ctypes as C
from pathlib import Path

def inventory():
 start=time.perf_counter_ns();objects=gc.get_objects();counts=collections.Counter();cycles=collections.Counter()
 for obj in objects:
  typ=type(obj);name=typ.__module__+'.'+typ.__qualname__;counts[name]+=1
  if isinstance(obj,C.Array):
   owners=getattr(obj,'_objects',None)
   if isinstance(owners,dict) and any(value is obj for value in owners.values()):cycles[name]+=1
 total=len(objects);del objects
 return dict(total=total,types=counts.most_common(100),ctypes_array_self_owners=cycles.most_common(100),elapsed_ms=(time.perf_counter_ns()-start)/1e6)
before=inventory()
try:runpy.run_path('work/camera/run_native_ordered_tail_candidate.py',run_name='__main__')
finally:
 after=inventory()
 Path('work/camera/prototype-runs/ordered-tail-boundary-inventory-20261009.json').write_text(json.dumps(dict(before=before,after=after,scope='Startup and post-shutdown tracked-object inventories only; cannot infer peak live graph, collected object types or allocation origin. No GC policy changes.'),indent=2))
print('BOUNDARY_INVENTORY',before['total'],after['total'])
