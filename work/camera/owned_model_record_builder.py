from owned_region_record import encode as encode_region
"""Reconstruct active scenery GPU records from immutable scene/source ownership."""
import ctypes as C,struct
from pathlib import Path
from owned_ordinary_model_visits import ordinary_model_visits
from owned_closed_scene_memory import scene_memory
from owned_model_assets import model_record_blocks,model_palette_equivalent
from owned_scenery_projection import SceneryProjection
from owned_motion_pairs import records
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32)

class ModelRecordBuilder:
 def __init__(self,rom):
  self._scene_memory=[]
  self.rom=bytes(rom);self.projection=SceneryProjection(self.rom);self.reciprocal=C.create_string_buffer(self.rom[0x627700:0x647700])
  self.lib=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()))
  self.lib.nfs_visibility_object_branch_prepare.argtypes=[C.c_void_p]*7
  self.lib.nfs_visibility_object_material_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
  self.lib.nfs_visibility_object_model_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
 def prepare_removed(self,older,newer,old_queue,new_queue,index):
  from owned_removed_scenery_visit import removed_scenery_visit
  visit=removed_scenery_visit(older,newer,old_queue,new_queue,index)
  return self._prepare(newer,new_queue,visit,False)
 def prepare_depth_hidden(self,older,newer,old_queue,new_queue,index):
  from owned_removed_scenery_visit import depth_hidden_scenery_visit
  visit=depth_hidden_scenery_visit(older,newer,old_queue,new_queue,index)
  return self._prepare(newer,new_queue,visit,False,False)
 def prepare_portal_hidden(self,older,newer,old_queue,new_queue,index):
  from owned_removed_scenery_visit import portal_hidden_scenery_visit
  visit=portal_hidden_scenery_visit(older,newer,old_queue,new_queue,index)
  return self._prepare(newer,old_queue,visit,False)
 def prepare_visit(self,scene,queue,visit):return self._prepare(scene,queue,visit,True)
 def prepare_far_hidden(self,scene,queue,visit):
  # Asset closure only for source-owned allocated flag2 scenery excluded
  # by original03002368 unsigned depth>=8192, before material selection.
  from owned_object_filter import depth_distance
  depth=depth_distance(visit['source'],scene.graph.graph.context[256:304])[0]
  if depth<8192 or depth!=visit['depth'] or not visit['allocated'] or not struct.unpack_from('<H',visit['source'],10)[0]&2:raise ValueError('Unverified far-hidden scenery')
  return self._prepare(scene,queue,visit,True,False)

 def _prepare(self,scene,queue,visit,require_chain,require_visibility=True):
  closed=scene.graph;state=closed.graph.context[:256];memory=next((memory for owner,memory in self._scene_memory if owner is closed),None)
  if memory is None:
   memory=scene_memory(closed,self.rom);self._scene_memory.append((closed,memory))
   if len(self._scene_memory)>2:self._scene_memory.pop(0)
  missing=[]
  owned_visits=ordinary_model_visits(closed,queue,True)
  if require_chain and not any(all(v[k]==visit[k] for k in ('object','source','parent','bounds','ordinal','position','dispatch','allocated')) for v in owned_visits):raise ValueError('Unowned scenery candidate visit')
  if not 30<=visit['dispatch']['model']<=36:raise ValueError('Unsupported model candidate')
  @Read
  def read(_,address,target,n):
   try:C.memmove(target,memory.read(address,n),n);return 1
   except ValueError:missing.append((address,n));return 0
  raw=bytearray(visit['source'])
  if not visit['allocated']:raw[136]=0 # Scratch slot for preparation; original source stays inactive.
  source=C.create_string_buffer(bytes(raw),164);owned_state=C.create_string_buffer(state,256)
  xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16);region=encode_region(queue[visit['ordinal']])
  if self.lib.nfs_visibility_object_branch_prepare(owned_state,source,region,closed.graph.context[256:304],xyz,C.byref(branch),child)!=1 or branch.value!=0:raise ValueError('Unverified scenery branch')
  material=(C.c_uint32*4)()
  if require_visibility:
   if self.lib.nfs_visibility_object_material_plan(owned_state,source,xyz,read,None,self.reciprocal,material)!=1 or material[3]!=0:raise ValueError('Unverified scenery material')
  else:
   # Asset preparation for verified hidden endpoint, not a draw visibility pass.
   # Original flag2 scenery selects effective material depth0 independently.
   if not struct.unpack_from('<H',visit['source'],10)[0]&2:raise ValueError('Unverified hidden material depth')
   self.lib.nfs_visibility_object_material.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
   self.lib.nfs_visibility_object_texture.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
   if not self.lib.nfs_visibility_object_material(source,struct.unpack_from('<I',state,36)[0],xyz[2],material) or material[1]!=0:raise ValueError('Unverified hidden material selection')
   texture=(C.c_uint32*2)();asset=memory.read(material[0],32)
   if not self.lib.nfs_visibility_object_texture(source,asset,None,struct.unpack_from('<I',state,4)[0],material[1],texture) or texture[1]!=0:raise ValueError('Unverified hidden scenery texture')
   material[2],material[3]=texture[0],texture[1]

  context=C.create_string_buffer(68)
  if self.lib.nfs_visibility_object_model_plan(owned_state,source,material,read,None,context)!=1:raise ValueError('Unowned scenery model context')
  if visit['allocated']:
   if scene.builders is None:raise ValueError('Missing scenery builder closure')
   base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0]
   builder=scene.builders.at(base+visit['object']*164,matrix_base+visit['source'][136]*48,closed.refresh)
   if struct.unpack_from('<h',builder.source,54)[0]!=visit['dispatch']['model']:raise ValueError('Scenery builder source changed')
   matrix=self.projection.matrix(builder.camera,builder.source,builder.initial_matrix)
  else:matrix=self.projection.matrix(closed.graph.context[256:304],visit['source'])
  blocks=model_record_blocks(context.raw,memory,matrix,closed.graph.context[304:368],visit['bounds'],closed.graph.context[384:896])
  if missing:raise ValueError('Incomplete scenery asset closure')
  return blocks

 def rebuild(self,scene,queue,frame):
  scene.match(frame);visits=ordinary_model_visits(scene.graph,queue);out={}
  for index,row in enumerate(records(frame)['records']):
   if row['kind']!=3:continue
   candidates=[]
   for visit in visits:
    model=visit['dispatch']['model'];offset=visit['dispatch']['descriptor']-0x08000000
    if 30<=model<=36 and bytes(row['blocks'][1])==self.rom[offset:offset+40]:candidates.append(visit)
   if not candidates:continue
   if len(candidates)!=1:raise ValueError('Ambiguous active scenery source')
   blocks=self.prepare_visit(scene,queue,candidates[0])
   if any(blocks[i]!=bytes(row['blocks'][i]) for i in range(11)) or not model_palette_equivalent(blocks,bytes(row['blocks'][11])):raise ValueError('Rebuilt model differs from captured source record')
   out[index]=dict(row,blocks=blocks)
  return out

