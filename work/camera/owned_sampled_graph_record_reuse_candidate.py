"""Bounded per-portal complete immutable wall record reuse; sampled visibility unchanged."""
import inspect,textwrap
import owned_sampled_graph_gpu as base
from owned_scene_gpu_wall import encode_draws as original_encode
class RecordCache:
 def __init__(self):self.records={};self.bytes=0;self.hits=0;self.misses=0
 def encode(self,context,draws,allow_deferred=False,cache=None):
  result=[]
  for ordinal,region,wall,scratch in draws:
   key=(region[0],wall.edge,tuple(region[1:5]),scratch,allow_deferred)
   entry=self.records.get(key)
   if entry is not None and entry[0]==context and entry[1]==wall:
    self.hits+=1;encoded=entry[2]
   else:
    self.misses+=1;encoded=original_encode(context,((ordinal,region,wall,scratch),),allow_deferred=allow_deferred,cache=cache)[0]
    size=len(encoded[1])
    if len(self.records)>=256 or self.bytes+size>8*1024*1024:self.records.clear();self.bytes=0
    if size<=8*1024*1024:
     if key in self.records:self.bytes-=len(self.records[key][2][1])
     self.records[key]=(context,wall,encoded);self.bytes+=size
   result.append(encoded)
  return tuple(result)
source=textwrap.dedent(inspect.getsource(base.sampled_graph_gpu_records))
source=source.replace('graph=portal.newer if alpha==1 else portal.older;result=[]',"graph=portal.newer if alpha==1 else portal.older;result=[]\n if not hasattr(portal,'_complete_wall_record_cache'):portal._complete_wall_record_cache=RecordCache()\n encode_draws=portal._complete_wall_record_cache.encode")
namespace=dict(base.sampled_graph_gpu_records.__globals__,RecordCache=RecordCache)
exec(compile(source,'sampled-graph-record-reuse','exec'),namespace)
sampled_graph_gpu_records=namespace['sampled_graph_gpu_records']
