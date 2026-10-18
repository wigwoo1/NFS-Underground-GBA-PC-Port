"""Read-only snapshots of loaded bounded transform caches; never clears caches."""
import sys
def snapshot():
 result={};seen=set()
 for name,module in list(sys.modules.items()):
  if not (name.startswith('owned_') or name=='sample_owned_motion'):continue
  for key,value in list(vars(module).items()):
   info=getattr(value,'cache_info',None)
   if not callable(info) or id(value) in seen:continue
   seen.add(id(value));row=info()
   result[name+'.'+key]=dict(hits=row.hits,misses=row.misses,maxsize=row.maxsize,currsize=row.currsize)
 return result
