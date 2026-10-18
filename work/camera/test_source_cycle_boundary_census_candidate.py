import gc,ctypes as C,types,collections,time,json,runpy
from pathlib import Path
def inventory():
 started=time.perf_counter_ns();objects=gc.get_objects();arrays=collections.Counter();callbacks=collections.Counter();selfclosures=collections.Counter();totals=collections.Counter();array_classes=collections.Counter()
 for obj in objects:
  typ=type(obj);totals[typ.__module__+'.'+typ.__qualname__]+=1
  if isinstance(obj,C.Array):arrays[(type(obj)._type_.__name__,len(obj))]+=1
  if isinstance(obj,C._CFuncPtr):callbacks[typ.__module__+'.'+typ.__qualname__]+=1
  if isinstance(obj,type):
   try:
    if issubclass(obj,C.Array):array_classes[(obj._type_.__name__,obj._length_)]+=1
   except (TypeError,AttributeError):pass
  if isinstance(obj,types.FunctionType) and obj.__closure__:
   for cell in obj.__closure__:
    try:
     if cell.cell_contents is obj:selfclosures[obj.__module__+'.'+obj.__qualname__]+=1
    except ValueError:pass
 total=len(objects);del objects
 return dict(total=total,array_instances=[dict(element=k[0],length=k[1],count=v) for k,v in arrays.most_common()],array_classes=[dict(element=k[0],length=k[1],count=v) for k,v in array_classes.most_common()],callbacks=callbacks.most_common(),direct_self_closures=selfclosures.most_common(),types=totals.most_common(25),elapsed_ms=(time.perf_counter_ns()-started)/1e6)
before=inventory()
try:runpy.run_path('work/camera/run_native_ordered_tail_candidate.py',run_name='__main__')
finally:
 after=inventory();out=dict(before=before,after=after,scope='Two startup/post-shutdown inventories only, outside active game wall clock. No GC policy change or retained object identities. Imports and legitimately retained diagnostics contribute; this cannot identify collected types, peak live allocation origin or exclusive stall cause.')
 Path('work/camera/prototype-runs/source-cycle-boundary-census-20261009.json').write_text(json.dumps(out,indent=2));print('CYCLE_CENSUS',before['total'],after['total'],after['direct_self_closures'])
