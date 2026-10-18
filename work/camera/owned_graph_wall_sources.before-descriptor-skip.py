"""World wall-edge sources decoded from complete owned graph/material snapshots."""
from dataclasses import dataclass
import struct
@dataclass(frozen=True)
class WallSource:
 descriptor:int
 edge:int
 vertices:bytes
 offsets:bytes
 animation:bytes
 resolved:bytes
 texture:bytes
 shift:int
 height:int
 address:int

def wall_sources(graph,*,validated=False,descriptors=None,material_cache=None):
 if not validated:graph.validate()
 if material_cache is not None and material_cache[0] is not graph:raise ValueError('Wall material cache owner mismatch')
 if material_cache is not None and material_cache[1] is not None:materials=material_cache[1]
 else:
  materials={};shared={};at=0
  while at<len(graph.materials):
   h=struct.unpack_from('<12I',graph.materials,at);body=graph.materials[at+48:at+120];at+=120;texture=b''
   if h[9]==1:texture=graph.materials[at:at+h[8]];at+=h[8];shared[h[10]]=texture
   elif h[9]==2:texture=shared[h[10]]
   materials[h[3]]=(body[32:40],body[40:72],texture,h[5],h[6],h[7])
  if material_cache is not None:material_cache[1]=materials
 result=[];at=offset=0
 while at<len(graph.geometry):
  identifier,n,_,_=struct.unpack_from('<4I',graph.geometry,at);at+=64;ring=graph.geometry[at:at+n*68];at+=n*68;offsets=graph.offsets[offset:offset+n*32];offset+=n*32
  if descriptors is not None and identifier not in descriptors:continue
  for edge in range(n):
   nxt=(edge+1)%n;vertex=ring[edge*68:(edge+1)*68];mi=struct.unpack_from('<H',vertex,44)[0]
   if mi==65535:continue
   animation,resolved,texture,shift,height,address=materials[mi]
   if not height:continue
   result.append(WallSource(identifier,edge,vertex+ring[nxt*68:(nxt+1)*68],offsets[edge*32:(edge+1)*32]+offsets[nxt*32:(nxt+1)*32],animation,resolved,texture,shift,height,address))
 return tuple(result)

def supplemental_wall_sources(bundle):
 from owned_scene_bundle import chunks
 bundle.validate();textures={}
 for _,raw in chunks(bundle.textures,'textures'):
  h=struct.unpack_from('<12I',raw);textures[(h[1],h[2],h[3],h[4])]=(h,raw)
 result=[]
 for h,raw in chunks(bundle.supplements,'supplements'):
  count=h[4];vertices=[raw[976+i*140:1044+i*140] for i in range(count)];offsets=[raw[1044+i*140:1076+i*140] for i in range(count)]
  for edge in range(count):
   th,tr=textures[(h[1],h[2],h[3],edge)]
   if not th[8]:continue
   nxt=(edge+1)%count
   result.append(WallSource(h[3],edge,vertices[edge]+vertices[nxt],offsets[edge]+offsets[nxt],tr[80:88],tr[88:120],tr[120:],th[7],th[8],th[9]))
 return tuple(result)

