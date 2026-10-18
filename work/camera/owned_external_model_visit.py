"""External car portal visit from exact endpoint object chains and rigid pose."""
import struct,math
from owned_scene_bundle import chunks
from owned_object_dispatch import select
from owned_external_source_motion import PreparedExternalSourceMotion

class PreparedExternalModelVisit:
 def __init__(self,scenes,sources,object_index,rom):
  self.scenes=tuple(scenes);self.sources=tuple(sources);self.object_index=object_index
  self.motion=PreparedExternalSourceMotion(self.scenes,self.sources,object_index)
  visits=[]
  for scene,packet in zip(self.scenes,self.sources):
   base=struct.unpack_from('<I',scene.graph.context,60)[0];source=packet.sources[base+object_index*164];found=[]
   for h,raw in chunks(scene.objects,'graph_objects'):
    for position in range(h[5]):
     if struct.unpack_from('<I',raw,128+position*168)[0]==object_index:
      if raw[132+position*168:296+position*168]!=source:raise ValueError('External chain/source mismatch')
      found.append((h[3],position))
   if len(found)!=1:raise ValueError('Ambiguous external chain visit')
   scratch=bytearray(source);scratch[136]=0
   dispatch=select(bytes(scratch),scene.graph.context[:256],0)
   if dispatch['kind']!='model':raise ValueError('Unsupported external visit dispatch')
   offset=dispatch['descriptor']-0x08000000
   if not 0<=offset<=len(rom)-40:raise ValueError('External descriptor outside ROM')
   visits.append((found[0],source,dispatch,bytes(rom[offset:offset+40])))
  # Object-chain membership is discrete original publication state. sample()
  # selects the older parent until the exact newer endpoint; rigid pose remains continuous.
  if visits[0][2]!=visits[1][2] or visits[0][3]!=visits[1][3]:raise ValueError('Unverified external asset transition')
  self.visits=tuple(visits)
 def sample(self,alpha,queue):
  if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('Invalid external visit alpha')
  endpoint=int(alpha==1);(parent,position),source,dispatch,_=self.visits[endpoint]
  regions=[(i,q) for i,q in enumerate(queue) if q[0]==parent and not q[5]&0x88 and q[1]<=q[2] and q[3]<=q[4]]
  if not regions:return None
  ordinal,q=regions[-1];matrix=self.motion.matrix(alpha);horizontal,depth=matrix[9],matrix[11]
  if depth<=0:return None
  if hasattr(self,'projection_vertices'):
   depths=[matrix[11]+x*matrix[2]+y*matrix[5]+z*matrix[8] for x,y,z in self.projection_vertices]
   if any(z<0 or z>0x6000 for z in depths):return None
  distance=(depth*depth+horizontal*horizontal)/256
  if not 0<=distance<2147483648:raise ValueError('External distance outside original range')
  return dict(object=self.object_index,parent=parent,position=position,ordinal=ordinal,bounds=tuple(q[1:5]),depth=depth,distance=distance,source=source,dispatch=dict(dispatch))
