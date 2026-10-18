"""Bounded child gen2 heap diagnostic, no GC policy changes."""
import types
import owned_child_road_wrapper_reuse_process_candidate as base
def request_child(*args):
 import gc,json,time,os,collections,sys
 from pathlib import Path
 rows=[];policy=(gc.isenabled(),gc.get_threshold());pending=None
 def callback(phase,info):
  nonlocal pending
  if info['generation']!=2:return
  if phase=='start':
   begin=time.perf_counter_ns();objects=gc.get_objects();counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in objects)
   large=[]
   for obj in objects:
    if type(obj) in (dict,list,tuple) and len(obj)>=500:
     detail=dict(type=type(obj).__name__,size=len(obj),id=id(obj))
     if type(obj) is dict:
      detail['key_types']=dict(collections.Counter(type(k).__name__ for k in obj))
      detail['value_types']=dict(collections.Counter(type(v).__name__ for v in obj.values()))
      owners=[]
      for ref in gc.get_referrers(obj):
       if type(ref) is dict:
        for key,value in list(ref.items()):
         if value is obj:owners.append(dict(type='dict',key=str(key)[:100],module=ref.get('__name__')))
       elif type(ref) is not list:owners.append(dict(type=type(ref).__module__+'.'+type(ref).__qualname__))
       if len(owners)>=8:break
      detail['owners']=owners[:8]
     large.append(detail)
   large.sort(key=lambda x:x['size'],reverse=True)
   frame=sys._getframe(1);stack=[]
   while frame and len(stack)<8:
    stack.append([Path(frame.f_code.co_filename).name,frame.f_code.co_name,frame.f_lineno]);frame=frame.f_back
   pending=dict(start_ns=begin,tracked=len(objects),counts=dict(counts),large=large[:16],stack=stack,census_end_ns=time.perf_counter_ns())
  elif pending:
   pending.update(end_ns=time.perf_counter_ns(),collected=info['collected'],uncollectable=info['uncollectable'])
   if len(rows)<32:rows.append(pending)
   pending=None
 gc.callbacks.append(callback)
 try:base.request_child(*args)
 finally:
  gc.callbacks.remove(callback);assert policy==(gc.isenabled(),gc.get_threshold())
  Path('work/camera/prototype-runs/child-gen2-heap-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),rows=rows,normal_gc_unchanged=True,scope='Heap census inside generation2 callback perturbs collection time; counts/stack/containers only, no retained source objects. Not cadence qualification.'),indent=2))
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
