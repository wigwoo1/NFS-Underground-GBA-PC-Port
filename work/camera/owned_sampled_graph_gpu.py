"""GPU wall records from complete main graph visibility at sampled rigid poses."""
import struct,os,time
from owned_wall_projection import projected
from owned_scene_gpu_wall import encode_draws
from owned_sampled_graph_wall_visibility import selected_graph_walls,wall_metadata
from owned_deferred_wall_policy import sampled_wall_emitted

def sampled_graph_gpu_records(portal,alpha):
 trace_enabled=os.environ.get('NFSUG_WALL_EDGE_PROFILE')=='1';stage_begin=time.perf_counter_ns() if trace_enabled else None
 if not trace_enabled:portal._last_sampled_graph_stages=None
 graph=portal.newer if alpha==1 else portal.older;result=[]
 if not hasattr(portal,"_gpu_wall_encoding_cache"):portal._gpu_wall_encoding_cache={}
 cache=portal._gpu_wall_encoding_cache
 if alpha in (0,1):
  draws,_=projected(graph,portal.reciprocal);draws=sorted(draws,key=lambda r:(-r[0],r[2].edge))
  selected_ns=time.perf_counter_ns() if trace_enabled else None
  for ordinal,region,wall,scratch in draws:
   vertices,record=encode_draws(graph.context,((ordinal,region,wall,scratch),),cache=cache)[0]
   result.append(dict(ordinal=ordinal,descriptor=region[0],edge=wall.edge,vertices=vertices,record=record,bounds=tuple(float(x) for x in region[1:5])))
 else:
  rings=wall_metadata(portal,graph)[0]
  selected=selected_graph_walls(portal,alpha);selected_ns=time.perf_counter_ns() if trace_enabled else None
  for candidate,visibility in selected:
   count=len(rings[candidate.descriptor][1])//68
   phase=0
   if visibility.flags&2 and (0 if count-candidate.edge>=32 else (1<<(count-candidate.edge))&255):
    desc=rings[candidate.descriptor][0]
    if candidate.region_flags&128 or desc[18]&8 or struct.unpack_from('<H',desc,6)[0]!=65535:raise ValueError('Unverified deferred wall child/object ordering')
    phase=2
   elif not sampled_wall_emitted(visibility.flags,candidate.edge,count):continue
   scratch=bytearray(52);struct.pack_into('<H',scratch,48,visibility.flags)
   region=(candidate.descriptor,0,239,0,159,0,0)
   vertices,record=encode_draws(graph.context,((candidate.ordinal,region,candidate.wall,bytes(scratch)),),allow_deferred=phase==2,cache=cache)[0]
   result.append(dict(surface_phase=phase,ordinal=candidate.ordinal,descriptor=candidate.descriptor,edge=candidate.edge,vertices=vertices,record=record,bounds=candidate.bounds))
 if trace_enabled:
  encoded_ns=time.perf_counter_ns();portal._last_sampled_graph_stages=dict(selection_ns=selected_ns-stage_begin,encoding_ns=encoded_ns-selected_ns,selected_count=len(draws) if alpha in (0,1) else len(selected),encoded_count=len(result),encoded_bytes=sum(len(row['record']) for row in result),static_cache_entries=len(cache))
 return tuple(result)
