"""Complete raw road candidates from graph ownership; no invocation visibility union."""
from owned_complete_road_candidates import RoadCandidate
from dataclasses import dataclass
import struct
def road_candidates(closed,memory):
 g=closed.graph;state=g.context[:256];face_base=struct.unpack_from('<I',state,28)[0];materials={};shared={};at=0;material_view=memoryview(g.materials)
 while at<len(g.materials):
  h=struct.unpack_from('<12I',g.materials,at);body=g.materials[at+48:at+120];at+=120;texture=None
  if h[9]==1:texture=material_view[at:at+h[8]];at+=h[8];shared[h[10]]=texture
  elif h[9]==2:texture=shared[h[10]]
  materials[h[3]]=(body[40:72],body[32:40],texture)
 out=[];texture_cache={};resolved_materials={};at=offset=0
 while at<len(g.geometry):
  identifier,n,_,_=struct.unpack_from('<4I',g.geometry,at);desc=g.geometry[at+16:at+64];at+=64;ring=g.geometry[at:at+n*68];at+=n*68;offsets=g.offsets[offset:offset+n*32];offset+=n*32
  for secondary,field in ((0,8),(1,4)):
   mi=struct.unpack_from('<H',desc,field)[0]
   if not mi:continue
   missing=[];fi=struct.unpack_from('<H',desc,10)[0];address=0 if fi==65535 else face_base+fi*20;face=bytes(20)
   if address:
    try:face=memory.read(address,20)
    except ValueError:face=None;missing.append('face20')
   if mi in resolved_materials:
    material,animation,texture,material_missing=resolved_materials[mi]
    missing.extend(material_missing)
   else:
    material_missing=[]
    material,animation,texture=materials.get(mi,(None,None,None))
    if material is None:material_missing.append('material32/animation8')
    if material is not None:
     shift=struct.unpack_from('<H',material,26)[0];height=struct.unpack_from('<H',material,10)[0]
     if shift>10 or not height:raise ValueError('Invalid road texture dimensions')
     texture_address=struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',material,4)[0]
     try:
      texture_key=(texture_address,(1<<shift)*height*2)
      if texture_key not in texture_cache:texture_cache[texture_key]=memory.read(*texture_key)
      full_texture=texture_cache[texture_key]
      if texture is not None and not full_texture.startswith(texture):raise ValueError('Conflicting road texture ownership')
      texture=full_texture
     except ValueError:material_missing.append('complete texture');texture=None
    if texture is None:material_missing.append('texture')
    resolved_materials[mi]=(material,animation,texture,tuple(material_missing))
    missing.extend(material_missing)
   out.append(RoadCandidate(identifier,secondary,mi,desc,ring,offsets,address,face,material,animation,texture,tuple(missing)))
 return tuple(out)

