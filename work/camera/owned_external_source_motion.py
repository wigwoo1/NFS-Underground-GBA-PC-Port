"""Rigid external car motion from immutable original boundary sources."""
import struct
from types import SimpleNamespace
from owned_model_builder_inputs import BuilderInputs
from owned_external_model_projection import external_model_matrix
from owned_scenery_motion import PreparedSceneryMotion

def boundary_external_pose(scene,sources,object_index):
 if (sources.epoch,sources.refresh,sources.source_refresh)!=(scene.epoch,scene.refresh,scene.graph.refresh):raise ValueError('Unpaired external source packet')
 if not isinstance(object_index,int) or object_index<0:raise ValueError('Invalid external source index')
 base=struct.unpack_from('<I',scene.graph.context,60)[0]
 address=base+object_index*164
 source=sources.sources[address]
 enabled,rotation=sources.external[address]
 flags=struct.unpack_from('<H',source,10)[0]
 # With flag2 absent, the original builder may retain an initial matrix.
 # A raw source boundary alone cannot prove that retained matrix.
 if not flags&2:raise ValueError('External source needs initial builder matrix')
 builder=BuilderInputs(scene.graph.refresh,0,address,0,source,scene.graph.context[256:304],bytes(48),enabled,rotation)
 return external_model_matrix(builder)

class PreparedExternalSourceMotion:
 def __init__(self,scenes,sources,object_index):
  scenes=tuple(scenes);sources=tuple(sources)
  if len(scenes)!=2 or len(sources)!=2:raise ValueError('Incomplete external source pair')
  if scenes[0].epoch!=scenes[1].epoch or scenes[0].graph.refresh>=scenes[1].graph.refresh:raise ValueError('Invalid external source clocks')
  raw=[]
  for scene,packet in zip(scenes,sources):
   address=struct.unpack_from('<I',scene.graph.context,60)[0]+object_index*164
   raw.append(packet.sources[address])
  if raw[0][54:56]!=raw[1][54:56] or raw[0][140:144]!=raw[1][140:144]:raise ValueError('External source identity changed')
  self.endpoint_poses=tuple(boundary_external_pose(s,p,object_index) for s,p in zip(scenes,sources))
  # Only transform blocks are consumed by this rigid component; these are
  # not renderable records or a claim of complete geometry preparation.
  pair=SimpleNamespace(object_index=object_index,older_blocks=(None,None,self.endpoint_poses[0]),newer_blocks=(None,None,self.endpoint_poses[1]))
  self._motion=PreparedSceneryMotion((pair,),*(s.graph.context[256:304] for s in scenes))
  self.object_index=object_index
 def matrix(self,alpha):return self._motion.matrix(self.object_index,alpha)
