"""Sampled parent clips/depth for supplemental calls owned at either endpoint."""
import struct
from owned_closed_supplemental_calls import calls
from owned_object_filter import depth_distance

def continuous_depth(source,camera):
 x=struct.unpack_from('<i',source,12)[0]>>8;z=struct.unpack_from('<i',source,20)[0]>>8
 return (x+camera[9])*camera[2]+(z+camera[11])*camera[8]

class SupplementalMotionPair:
 def __init__(self,older,newer,old_supplements,new_supplements,portal_pair):
  self.portal=portal_pair;self.old=calls(older,old_supplements);self.new=calls(newer,new_supplements)
  self.ma=older.graph.context[256:304];self.mb=newer.graph.context[256:304]
  self.known={}
  for c in self.old+self.new:
   key=(c.parent_descriptor,c.object_index,c.descriptor)
   if key in self.known and self.known[key].source[12:24]!=c.source[12:24]:raise ValueError('Unverified moving supplemental object')
   self.known.setdefault(key,c)
 def sample(self,alpha):
  queue=self.portal.sample(alpha)
  if alpha in (0,1):
   endpoint=self.old if alpha==0 else self.new
   return tuple(dict(parent=c.parent_descriptor,object=c.object_index,descriptor=c.descriptor,bounds=tuple(float(x) for x in c.parent_region[1:5]),depth=float(depth_distance(c.source,self.ma if alpha==0 else self.mb)[0])) for c in endpoint)
  _,camera,_=self.portal.motion.sample(alpha);out=[]
  for c in self.known.values():
   parents=[q for q in queue if q[0]==c.parent_descriptor and not q[5]&8]
   if len(parents)>1:raise ValueError('Ambiguous sampled supplemental parent')
   if not parents:continue
   da=depth_distance(c.source,self.ma)[0];db=depth_distance(c.source,self.mb)[0]
   depth=continuous_depth(c.source,camera)+(1-alpha)*(da-continuous_depth(c.source,self.portal.endpoints[0]))+alpha*(db-continuous_depth(c.source,self.portal.endpoints[1]))
   if depth<=0:continue
   q=parents[0]
   if q[1]>q[2] or q[3]>q[4]:continue
   out.append(dict(parent=c.parent_descriptor,object=c.object_index,descriptor=c.descriptor,bounds=tuple(float(x) for x in q[1:5]),depth=depth))
  return tuple(out)
