"""Enumerate complete sampled supplemental candidates with resolved selector12 eligibility."""
from dataclasses import dataclass
import struct,time
from owned_thread_cycles import read as thread_cycles
from owned_supplemental_dependencies import dependencies
from owned_complete_supplemental_sources import complete_wall_sources
from owned_object_filter import depth_distance
from owned_supplemental_eligibility import supplemental_eligibility
from owned_motion_supplemental import continuous_depth
@dataclass(frozen=True)
class SupplementalCandidate:
 parent:int
 object:int
 descriptor:int
 bounds:tuple
 depth:float
 distance:float
 eligibility:str
 wall_edges:tuple
 ordinal:int=0

class CompleteSupplementalCandidates:
 def __init__(self,older,newer,old_supplements,new_supplements,portal,rom):
  self.portal=portal;self.scenes=(older,newer);self.supplements=(old_supplements,new_supplements)
  self.construct_stages=[];started=time.perf_counter_ns();cycles=thread_cycles()
  def stage(name):
   nonlocal started,cycles
   end=time.perf_counter_ns();now=thread_cycles()
   self.construct_stages.append(dict(name=name,started_ns=started,completed_ns=end,wall_ns=end-started,thread_cycles=now-cycles))
   started=end;cycles=now
  old_dependencies=dependencies(older);stage('older_dependencies')
  new_dependencies=dependencies(newer);stage('newer_dependencies')
  self.dependencies=(old_dependencies,new_dependencies)
  old_assets=complete_wall_sources(older,old_supplements,rom);stage('older_wall_assets')
  new_assets=complete_wall_sources(newer,new_supplements,rom);stage('newer_wall_assets')
  self.assets=(old_assets,new_assets)
  a={(d.parent_descriptor,d.object_index,d.descriptor):d for d in self.dependencies[0]}
  b={(d.parent_descriptor,d.object_index,d.descriptor):d for d in self.dependencies[1]}
  if a.keys()!=b.keys():raise ValueError('Supplemental object topology changed')
  for key in a:
   if a[key].source[12:24]!=b[key].source[12:24]:raise ValueError('Unverified moving supplemental object')
  # Retain immutable endpoint lookup order for this scene pair only.
  self._asset_edges=[];self._positions=[]
  for assets,rows in zip(self.assets,self.dependencies):
   edges={}
   for wall in assets:edges.setdefault(wall.descriptor,[]).append(wall)
   self._asset_edges.append({key:tuple(value) for key,value in edges.items()})
   self._positions.append({(d.parent_descriptor,d.object_index,d.descriptor):i for i,d in enumerate(rows)})
  stage('topology_and_indexes')
 def _endpoint_depth(self,source,endpoint):
  if not hasattr(self,'_endpoint_depth_cache'):self._endpoint_depth_cache=({}, {})
  cache=self._endpoint_depth_cache[endpoint];key=bytes(source)
  if key not in cache:cache[key]=depth_distance(source,self.scenes[endpoint].graph.context[256:304])
  return cache[key]
 def sample(self,alpha):
  if not 0<=alpha<=1:raise ValueError('Invalid motion alpha')
  queue=self.portal.sample(alpha);_,camera,_=self.portal.motion.sample(alpha)
  endpoint=1 if alpha==1 else 0;out=[];parents_by_descriptor={}
  for i,q in enumerate(queue):
   if not q[5]&8:parents_by_descriptor.setdefault(q[0],[]).append((i,q))
  for d in self.dependencies[endpoint]:
   parents=parents_by_descriptor.get(d.parent_descriptor,())
   for ordinal,q in parents:
    if q[1]>q[2] or q[3]>q[4]:continue
    da=self._endpoint_depth(d.source,0)[0]
    db=self._endpoint_depth(d.source,1)[0]
    depth=da if alpha==0 else db if alpha==1 else continuous_depth(d.source,camera)+(1-alpha)*(da-continuous_depth(d.source,self.portal.endpoints[0]))+alpha*(db-continuous_depth(d.source,self.portal.endpoints[1]))
    if depth<=0:continue
    decision=supplemental_eligibility(d.source)
    if decision in ('inactive','hidden'):continue
    distance=self._endpoint_depth(d.source,endpoint)[1] if alpha in (0,1) else None
    if distance is None:
     x=struct.unpack_from('<i',d.source,12)[0]>>8;z=struct.unpack_from('<i',d.source,20)[0]>>8
     horizontal=lambda m:(x+m[9])*m[0]+(z+m[11])*m[6]
     ha=self._endpoint_depth(d.source,0)[2];hb=self._endpoint_depth(d.source,1)[2]
     h=horizontal(camera)+(1-alpha)*(ha-horizontal(self.portal.endpoints[0]))+alpha*(hb-horizontal(self.portal.endpoints[1]))
     square=depth*depth+h*h
     if square>=0x80000000:raise ValueError('Unverified sampled object distance wrap')
     distance=square/256+(1-alpha)*(self._endpoint_depth(d.source,0)[1]-(da*da+ha*ha)/256)+alpha*(self._endpoint_depth(d.source,1)[1]-(db*db+hb*hb)/256)
    out.append(SupplementalCandidate(d.parent_descriptor,d.object_index,d.descriptor,tuple(float(x) for x in q[1:5]),depth,distance,decision,self._asset_edges[endpoint].get(d.descriptor,()),ordinal))
  # Original region passes walk the portal queue backwards. Within a
  # parent, decreasing distance insertion reverses equal-distance chains.
  positions=self._positions[endpoint]
  out.sort(key=lambda c:(-c.ordinal,-c.distance,-positions[c.parent,c.object,c.descriptor]))
  return tuple(out)




