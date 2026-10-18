import gc,time
from collections import Counter

def snapshot(boundary):
 begin=time.perf_counter_ns();objects=gc.get_objects();types=Counter();list_sizes=Counter();dict_shapes=Counter()
 for value in objects:
  types[type(value).__module__+'.'+type(value).__name__]+=1
  if type(value) is list:list_sizes['empty' if not value else '1-8' if len(value)<=8 else '9-64' if len(value)<=64 else '65-1024' if len(value)<=1024 else 'over1024']+=1
  elif type(value) is dict and 0<len(value)<=20 and all(type(k) is str for k in value):dict_shapes[tuple(sorted(value))]+=1
 total=len(objects);del objects
 return dict(boundary=boundary,total=total,types=types.most_common(25),list_size_bins=dict(list_sizes),small_dict_key_shapes=dict_shapes.most_common(15),begin_ns=begin,end_ns=time.perf_counter_ns(),scope='Same live Python process tracked objects, keys/types/counts only; temporary snapshot references and traversal overhead perturb scheduling. Not root attribution or performance control.')
