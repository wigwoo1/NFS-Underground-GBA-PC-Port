"""Immutable scene plus independently owned model payload publication unit."""
from dataclasses import dataclass
import struct,zlib
from owned_scene_bundle import SceneBundle
from owned_scene_model_binding import attach_meshes
from owned_scene_gpu_model import encode,palette
from owned_model_mesh import ModelMesh
FIELDS=('scene','poses','textures','palettes','meshes')
@dataclass(frozen=True)
class ModelScenePacket:
 scene:bytes
 poses:bytes
 textures:bytes
 palettes:bytes
 meshes:bytes
 def __post_init__(self):
  for name in FIELDS:object.__setattr__(self,name,bytes(getattr(self,name)))
 def gpu_records(self):
  bundle=SceneBundle.decode(self.scene);camera=bundle.validate().context[256:304];assets={};offset=0
  for data,stride in ((self.poses,292),(self.palettes,756)):
   if len(data)%stride:raise ValueError('Truncated scene companion')
   if any(data[o+196:o+244]!=camera for o in range(0,len(data),stride)):raise ValueError('Foreign scene companion')
  cursor=0
  while cursor<len(self.textures):
   if cursor+548>len(self.textures):raise ValueError('Truncated scene texture')
   size=struct.unpack_from('<I',self.textures,cursor+36)[0]
   if size>0x80000 or cursor+548+size>len(self.textures) or self.textures[cursor+500:cursor+548]!=camera:raise ValueError('Foreign or invalid scene texture')
   cursor+=548+size
  while offset<len(self.meshes):
   if offset+4>len(self.meshes):raise ValueError('Truncated mesh section')
   n=struct.unpack_from('<I',self.meshes,offset)[0];offset+=4
   if n>1024*1024 or offset+n>len(self.meshes):raise ValueError('Invalid mesh section')
   data=self.meshes[offset:offset+n];offset+=n;mesh=ModelMesh.decode(data);key=(mesh.model,mesh.variant)
   if key in assets:raise ValueError('Duplicate mesh identity')
   assets[key]=data
  plan=attach_meshes(bundle,self.poses,self.textures,assets)
  return tuple(encode(bundle,draw,palette(bundle,draw,self.palettes)) for draw in plan)
 def encode(self):
  self.gpu_records();payload=b''.join(getattr(self,f) for f in FIELDS)
  return struct.pack('<8I',0x3143534e,1,*(len(getattr(self,f)) for f in FIELDS),zlib.crc32(payload))+payload
 @classmethod
 def decode(cls,encoded):
  raw=bytes(encoded)
  if len(raw)<32 or len(raw)>32*1024*1024:raise ValueError('Invalid model scene length')
  h=struct.unpack_from('<8I',raw)
  if h[:2]!=(0x3143534e,1) or sum(h[2:7])+32!=len(raw) or zlib.crc32(raw[32:])!=h[7]:raise ValueError('Invalid model scene header')
  fields=[];offset=32
  for n in h[2:7]:fields.append(raw[offset:offset+n]);offset+=n
  packet=cls(*fields);packet.gpu_records();return packet

 @classmethod
 def compact(cls,scene,poses,textures,palettes,meshes):
  bundle=SceneBundle.decode(scene);camera=bundle.validate().context[256:304]
  def fixed(raw,stride):
   if len(raw)%stride:raise ValueError('Truncated capture companion')
   return b''.join(raw[o:o+stride] for o in range(0,len(raw),stride) if raw[o+196:o+244]==camera)
  selected=[];cursor=0
  while cursor<len(textures):
   if cursor+548>len(textures):raise ValueError('Truncated capture texture')
   n=struct.unpack_from('<I',textures,cursor+36)[0]
   if n>0x80000 or cursor+548+n>len(textures):raise ValueError('Invalid capture texture')
   if textures[cursor+500:cursor+548]==camera:selected.append(textures[cursor:cursor+548+n])
   cursor+=548+n
  from owned_scene_dispatch import draws
  keys={(r['dispatch']['model'],r['dispatch']['variant']) for r in draws(bundle) if r['dispatch']['kind']=='model'}
  assets=[];cursor=0
  while cursor<len(meshes):
   if cursor+4>len(meshes):raise ValueError('Truncated capture mesh')
   n=struct.unpack_from('<I',meshes,cursor)[0];cursor+=4
   if cursor+n>len(meshes):raise ValueError('Truncated capture mesh')
   raw=meshes[cursor:cursor+n];cursor+=n;mesh=ModelMesh.decode(raw)
   if (mesh.model,mesh.variant) in keys:assets.append(struct.pack('<I',n)+raw)
  packet=cls(scene,fixed(poses,292),b''.join(selected),fixed(palettes,756),b''.join(assets));packet.gpu_records();return packet
