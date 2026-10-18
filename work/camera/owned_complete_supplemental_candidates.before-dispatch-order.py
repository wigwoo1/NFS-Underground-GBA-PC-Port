"""Enumerate complete sampled supplemental candidates with explicit eligibility gaps."""
from dataclasses import dataclass
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
 eligibility:str
 wall_edges:tuple

class CompleteSupplementalCandidates:
 def __init__(self,older,newer,old_supplements,new_supplements,portal,rom):
  self.portal=portal;self.scenes=(older,newer)
  self.dependencies=(dependencies(older),dependencies(newer))
  self.assets=(complete_wall_sources(older,old_supplements,rom),complete_wall_sources(newer,new_supplements,rom))
  a={(d.parent_descriptor,d.object_index,d.descriptor):d for d in self.dependencies[0]}
  b={(d.parent_descriptor,d.object_index,d.descriptor):d for d in self.dependencies[1]}
  if a.keys()!=b.keys():raise ValueError('Supplemental object topology changed')
  for key in a:
   if a[key].source[12:24]!=b[key].source[12:24]:raise ValueError('Unverified moving supplemental object')
 def sample(self,alpha):
  if not 0<=alpha<=1:raise ValueError('Invalid motion alpha')
  queue=self.portal.sample(alpha);_,camera,_=self.portal.motion.sample(alpha)
  endpoint=1 if alpha==1 else 0;out=[]
  for d in self.dependencies[endpoint]:
   parents=[q for q in queue if q[0]==d.parent_descriptor and not q[5]&8]
   if len(parents)>1:raise ValueError('Ambiguous supplemental parent')
   if not parents:continue
   q=parents[0]
   if q[1]>q[2] or q[3]>q[4]:continue
   da=depth_distance(d.source,self.scenes[0].graph.context[256:304])[0]
   db=depth_distance(d.source,self.scenes[1].graph.context[256:304])[0]
   depth=da if alpha==0 else db if alpha==1 else continuous_depth(d.source,camera)+(1-alpha)*(da-continuous_depth(d.source,self.portal.endpoints[0]))+alpha*(db-continuous_depth(d.source,self.portal.endpoints[1]))
   if depth<=0:continue
   decision=supplemental_eligibility(d.source)
   if decision in ('inactive','hidden'):continue
   out.append(SupplementalCandidate(d.parent_descriptor,d.object_index,d.descriptor,tuple(float(x) for x in q[1:5]),depth,decision,tuple(w for w in self.assets[endpoint] if w.descriptor==d.descriptor)))
  return tuple(out)

