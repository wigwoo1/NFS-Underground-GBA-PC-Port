"""Short collectible-object attribution window; explicitly not a timing control."""
import gc,runpy,json,collections,ctypes as C,time
from pathlib import Path
from live_owned_gpu_worker import LiveOwnedGPUWorker
original=LiveOwnedGPUWorker.submit;before=gc.get_debug();active=False;saved=False;count=0

def submit(self,*args,**kwargs):
 global active,saved,count
 count+=1
 if count==80:
  assert not gc.garbage,'Preexisting garbage would contaminate diagnostic'
  gc.collect();gc.set_debug(before|gc.DEBUG_SAVEALL);active=True
 if active and not saved and (count>=100 or len(gc.garbage)>=20000):
  gc.set_debug(before);active=False;gc.collect();saved=True
  types=collections.Counter();shapes=collections.Counter();arrays=collections.Counter();functions=collections.Counter()
  for value in gc.garbage:
   t=type(value);types[t.__module__+'.'+t.__qualname__]+=1
   if t is dict and len(value)<=20 and all(type(k) is str for k in value):shapes[tuple(sorted(value))]+=1
   if isinstance(value,type) and issubclass(value,C.Array):arrays[(value._type_.__name__,value._length_)]+=1
   if t.__name__=='function':functions[value.__module__+'.'+value.__qualname__]+=1
  out=dict(result='SHORT_LIVE_COLLECTIBLE_OBJECT_ATTRIBUTION',submissions=[80,count],objects=len(gc.garbage),types=types.most_common(30),dict_shapes=shapes.most_common(20),array_types=arrays.most_common(30),functions=functions.most_common(20),scope='DEBUG_SAVEALL over at most20 scene submissions, earlier cutoff after observed20000 retained objects; automatic collection remains enabled. Explicit collect and retained garbage perturb runtime: no timing or speed qualification. Only unreachable collectible objects, no current ownership attribution.')
  Path('work/camera/prototype-runs/short-live-cycle-attribution-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
  value=None;gc.garbage.clear();gc.collect()
 return original(self,*args,**kwargs)
LiveOwnedGPUWorker.submit=submit
try:
 runpy.run_path('work/camera/run_native_caller_stages_candidate.py',run_name='__main__')
 assert saved,'Diagnostic window not reached'
finally:
 LiveOwnedGPUWorker.submit=original;gc.set_debug(before)
 if active:gc.garbage.clear();gc.collect()
