"""Bind bounded original model draw payloads to immutable source scene dispatch."""
from dataclasses import dataclass
import struct
from owned_graph_packet import GraphPacket
from owned_scene_dispatch import draws
@dataclass(frozen=True)
class ModelDraw:
 region:int
 index:int
 descriptor:int
 source:bytes
 matrix:bytes
 material:bytes
 texture:bytes
 def __post_init__(self):
  for name in ('source','matrix','material','texture'):object.__setattr__(self,name,bytes(getattr(self,name)))

def identity(source):
 # Raw object ID plus inputs consumed by model/texture dispatch and pose selection.
 return source[:2]+source[10:24]+source[54:56]+source[68:74]+source[132:137]

def bind(bundle,pose_bytes,texture_bytes):
 camera=GraphPacket.decode(bundle.graph).context[256:304];poses={};textures={}
 if len(pose_bytes)%292:raise ValueError('Truncated object pose')
 for offset in range(0,len(pose_bytes),292):
  h=struct.unpack_from('<8I',pose_bytes,offset);body=pose_bytes[offset+32:offset+292]
  if h[0]!=0x31504f4e or h[6]!=260 or h[7]!=1:raise ValueError('Invalid object pose')
  if body[164:212]!=camera:continue
  source=identity(body[:164])
  if source in poses:raise ValueError('Duplicate object pose')
  poses[source]=body[212:260]
 offset=0
 while offset<len(texture_bytes):
  if offset+548>len(texture_bytes):raise ValueError('Truncated object texture')
  h=struct.unpack_from('<12I',texture_bytes,offset);size=h[9]
  if h[0]!=0x31544f4e or h[10]!=1 or h[7]>10 or h[8]>1024 or size!=(1<<h[7])*h[8] or size>0x80000 or offset+548+size>len(texture_bytes):raise ValueError('Invalid object texture')
  body=texture_bytes[offset+48:offset+548];payload=texture_bytes[offset+548:offset+548+size];offset+=548+size
  if body[452:500]!=camera:continue
  source=identity(body[:164])
  if source in textures:raise ValueError('Duplicate object texture')
  textures[source]=(body[420:452],payload)
 result=[]
 for row in draws(bundle):
  if row['dispatch']['kind']!='model':continue
  source=row['source'];key=identity(source)
  if key not in poses or key not in textures:raise ValueError('Missing source-identical model payload')
  material,texture=textures[key]
  result.append(ModelDraw(row['region'],row['index'],row['dispatch']['descriptor'],source,poses[key],material,texture))
 if len(result)!=len(poses) or len(result)!=len(textures):raise ValueError('Unbound scene model payload')
 return tuple(result)

@dataclass(frozen=True)
class MeshedModelDraw:
 draw:ModelDraw
 mesh:object

def attach_meshes(bundle,pose_bytes,texture_bytes,assets):
 from owned_model_mesh import ModelMesh
 plan=bind(bundle,pose_bytes,texture_bytes);dispatch={(row['region'],row['index']):row['dispatch'] for row in draws(bundle)};result=[]
 for draw in plan:
  choice=dispatch[(draw.region,draw.index)];key=(choice['model'],choice['variant'])
  if key not in assets:raise ValueError('Missing selected model mesh')
  mesh=ModelMesh.decode(assets[key])
  if (mesh.model,mesh.variant)!=key:raise ValueError('Mismatched model mesh identity')
  result.append(MeshedModelDraw(draw,mesh))
 return tuple(result)
