"""Opt-in bounded collector census; scans perturb timing, never a cadence test."""
import gc,time,sys,os
from collections import Counter
count=0
def snapshot():
 global count
 count+=1
 if count not in (1,100,200,300,400,500,600,700):return None
 if os.environ.get('NFSUG_CHILD_CENSUS_GENERATIONS')=='1':
  from child_generation_census_candidate import snapshot as generation_snapshot
  result=dict(request_number=count,**generation_snapshot())
  if count==400 and os.environ.get('NFSUG_CHILD_SCENE_REFERRERS')=='1':
   from child_scene_referrers_candidate import snapshot as referrer_snapshot
   result['scene_referrers']=referrer_snapshot()
  if os.environ.get('NFSUG_CHILD_SCENE_MEMORY_TRACE')=='1':
   import child_scene_memory_trace_candidate
   result['scene_memory_trace']=child_scene_memory_trace_candidate.snapshot()
  return result
 begin=time.perf_counter_ns();objects=gc.get_objects();types=Counter();sizes=Counter()
 for obj in objects:
  name=type(obj).__module__+'.'+type(obj).__qualname__;types[name]+=1
  try:sizes[name]+=sys.getsizeof(obj)
  except (TypeError,ValueError):pass
 total=len(objects);del objects
 return dict(request_number=count,elapsed_ns=time.perf_counter_ns()-begin,tracked_objects=total,types=[dict(name=k,count=n,shallow_bytes=sizes[k]) for k,n in types.most_common(30)],scope='Collector-tracked objects held at completed request before optional idle cleanup. Shallow sizes exclude referenced buffers and are not total retained memory. Scan perturbs timing; no ownership/cause or cadence claim.')



