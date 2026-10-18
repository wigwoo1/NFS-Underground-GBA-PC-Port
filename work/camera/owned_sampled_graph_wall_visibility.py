"""Sample complete graph wall visibility from owned offset rings and rigid camera."""
import struct,time,os
from owned_thread_cycles import read as thread_cycles
from owned_motion_wall_regions import wall_region_candidates
from owned_continuous_wall_visibility import sampled_edge,select_wall

def graph_offset_rings(graph):
 result={};at=offset=0
 while at<len(graph.geometry):
  identifier,n,_,_=struct.unpack_from('<4I',graph.geometry,at);at+=64+n*68
  result[identifier]=graph.offsets[offset:offset+n*32];offset+=n*32
 return result

def wall_metadata(portal,graph):
 if not hasattr(portal,'_wall_metadata_cache'):portal._wall_metadata_cache=[]
 for owner,value in portal._wall_metadata_cache:
  if owner is graph:return value
 rings={};offset_rings={};at=offset=0;bases={};cursor=0
 while at<len(graph.geometry):
  identifier,n,_,_=struct.unpack_from('<4I',graph.geometry,at);desc=graph.geometry[at+16:at+64];at+=64;ring=graph.geometry[at:at+n*68];at+=n*68;offset_ring=graph.offsets[offset:offset+n*32];rings[identifier]=(desc,ring,offset_ring);offset_rings[identifier]=offset_ring;offset+=n*32
 while cursor<len(graph.materials):
  h=struct.unpack_from('<12I',graph.materials,cursor);bases[h[3]]=graph.materials[cursor+48:cursor+80];cursor+=120+(h[8] if h[9]==1 else 0)
 from types import MappingProxyType
 value=(MappingProxyType(rings),MappingProxyType(bases),MappingProxyType(offset_rings))
 portal._wall_metadata_cache.append((graph,value))
 if len(portal._wall_metadata_cache)>2:portal._wall_metadata_cache.pop(0)
 return value

def selected_graph_walls(portal,alpha,*,queue=None):
 stages=[];portal._last_wall_selection_stages=stages;start=time.perf_counter_ns();cycles_start=thread_cycles()
 def stage(name,count):
  nonlocal start,cycles_start
  end=time.perf_counter_ns();cycles=thread_cycles();stages.append(dict(name=name,count=count,started_ns=start,completed_ns=end,wall_ns=end-start,thread_cycles=cycles-cycles_start));start=end;cycles_start=cycles
 graph=portal.newer if alpha==1 else portal.older
 if alpha not in (0,1) and wall_metadata(portal,portal.older)[2]!=wall_metadata(portal,portal.newer)[2]:raise ValueError('Unverified moving graph vertex offsets')
 rings,bases,_=wall_metadata(portal,graph)
 camera=() if alpha in (0,1) else tuple(portal.motion.sample(alpha)[1])
 old_camera=portal.older.context[256:304];new_camera=portal.newer.context[256:304]
 stage('metadata_and_camera',0)
 selected=[];pending=[];calls=[];edge_profile=os.environ.get('NFSUG_WALL_EDGE_PROFILE')=='1';edge_rows=[]
 candidates=wall_region_candidates(portal,alpha,queue=queue);stage('candidate_generation',len(candidates))
 if getattr(portal,'_last_wall_candidate_stages',None):stages[-1]['candidate_stages']=portal._last_wall_candidate_stages
 for candidate in candidates:
  desc,ring,offsets=rings[candidate.descriptor]
  edge_started=time.perf_counter_ns() if edge_profile else None
  edge=sampled_edge(candidate.wall,ring,old_camera,new_camera,camera,portal.endpoints,alpha,offsets)
  if edge_profile:edge_rows.append(dict(descriptor=candidate.descriptor,edge=candidate.edge,ring_vertices=len(ring)//68,elapsed_ns=time.perf_counter_ns()-edge_started))
  if edge is None:continue
  material=struct.unpack_from('<H',candidate.wall.vertices,44)[0]
  pending.append(candidate);calls.append((candidate.wall,desc,edge,graph.context[304:368],candidate.bounds,bases[material],portal.reciprocal))
 from owned_wall_visibility_candidate import batch
 stage('candidate_edges',len(calls))
 if edge_profile:stages[-1]['sampled_edge_profiles']=sorted(edge_rows,key=lambda row:row['elapsed_ns'],reverse=True)[:128]
 outputs=batch(calls);stage('visibility_batch',len(outputs))
 for candidate,visibility in zip(pending,outputs):
  if visibility.visible:selected.append((candidate,visibility))
 result=tuple(sorted(selected,key=lambda row:(-row[0].ordinal,row[0].edge)));stage('selection_and_order',len(result));return result
