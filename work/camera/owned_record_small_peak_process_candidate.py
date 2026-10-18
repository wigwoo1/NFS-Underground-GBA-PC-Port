import types
import owned_child_road_wrapper_reuse_process_candidate as base
def request_child(*args):
 import owned_motion_pairs as module
 import gc,json,os,time
 from pathlib import Path
 from owned_record_small_blocks_candidate import decode_records
 module._decode_records=decode_records
 import owned_record_miss_container_reuse_install_candidate
 previous=module.records
 totals=dict(calls=0,max_entries=0,max_blocks=0,max_tracked_blocks=0,max_copied_bytes=0)
 def measured(frame,trace=None):
  result=previous(frame,trace)
  entries=getattr(module._record_cache,'entries',[])
  blocks=tracked=copied=0
  for owner,header,rows in entries:
   for kind,context,values,key in rows:
    for block in values:
     blocks+=1;tracked+=gc.is_tracked(block)
     if type(block) is bytes:copied+=len(block)
  totals['calls']+=1
  for name,value in [('entries',len(entries)),('blocks',blocks),('tracked_blocks',tracked),('copied_bytes',copied)]:
   totals['max_'+name]=max(totals['max_'+name],value)
  return result
 module.records=measured
 # Already imported consumers hold direct aliases; replace only exact function identities.
 import sys
 aliases=[]
 for mod in tuple(sys.modules.values()):
  if mod is None or not getattr(mod,'__name__','').startswith('owned_'):continue
  for key,value in tuple(vars(mod).items()):
   if value is previous:
    aliases.append((mod,key));setattr(mod,key,measured)
 try:base.request_child(*args)
 finally:
  for mod,key in aliases:setattr(mod,key,previous)
  module.records=previous
  Path('work/camera/prototype-runs/record-small-peak-'+str(time.time_ns())+'.json').write_text(json.dumps(dict(pid=os.getpid(),totals=totals,scope='Bounded scalar counters after record calls before cleanup; instrumentation scans at most four cached frames and perturbs timing.'),indent=2))
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
