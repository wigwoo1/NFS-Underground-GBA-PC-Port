"""Diagnostic only: normal-GC full parent census; no object references retained."""
import gc,collections,sys,json,time
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as worker
Session=worker.NativeSourceWorker._run.__globals__['NativeSourceSession'];original=Session.prepare
rows=[];count=0;policy=(gc.isenabled(),gc.get_threshold())
def census(phase):
 begin=time.perf_counter_ns();objects=gc.get_objects();counts=collections.Counter();largest=[]
 for obj in objects:
  name=type(obj).__module__+'.'+type(obj).__qualname__;counts[name]+=1
  if type(obj) in (dict,list,tuple) and len(obj)>=1000:
   if type(obj) is dict:
    description=[str(k)[:80] for k in list(obj)[:6] if type(k) in (str,int)]
    module=obj.get('__name__');module=module if type(module) is str else None
   else:description=[type(x).__module__+'.'+type(x).__qualname__ for x in obj[:3]];module=None
   largest.append(dict(type=name,length=len(obj),keys_or_element_types=description,module=module,size=sys.getsizeof(obj)))
 total=len(objects);del objects,obj
 assert policy==(gc.isenabled(),gc.get_threshold())
 rows.append(dict(phase=phase,prepare_count=count,begin_ns=begin,end_ns=time.perf_counter_ns(),tracked_total=total,types=dict(counts),largest_containers=sorted(largest,key=lambda x:x['length'],reverse=True)[:24]))
def prepare(self,*args,**kwargs):
 global count
 result=original(self,*args,**kwargs);count+=1
 if count in (1,300,600):census('active_after_prepare')
 return result
Session.prepare=prepare
def save():
 census('after_shutdown')
 out=dict(result='DIAGNOSTIC_FULL_PARENT_NORMAL_GC_HEAP',rows=rows,gc_policy_unchanged=policy==(gc.isenabled(),gc.get_threshold()),scope='Full live parent diagnostic census, bounded4snapshots and24largecontainer descriptions each, no object references retained. Census stalls instrumentation; not gameplaycadence qualification.')
 p=Path('work/camera/prototype-runs')/('full-parent-heap-'+str(time.time_ns())+'.json');p.write_text(json.dumps(out,indent=2));print('PARENT_HEAP_MANIFEST',p,flush=True)
