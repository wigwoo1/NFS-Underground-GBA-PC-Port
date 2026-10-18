from owned_region_record import encode as encode_region
"""Complete external-model candidate assets from closed source memory."""
import ctypes as C,struct
from owned_model_record_builder import ModelRecordBuilder,Read
from owned_closed_scene_memory import scene_memory
from owned_model_assets import model_record_blocks
from owned_external_source_motion import boundary_external_pose

def external_record_candidate(closed,sources,object_index,region,rom,hidden_depth=False):
 matrix=boundary_external_pose(closed,sources,object_index)
 base=struct.unpack_from('<I',closed.graph.context,60)[0]
 raw=bytearray(sources.sources[base+object_index*164])
 # Context pointer scratch slot is solely for asset preparation. The owned
 # raw allocation, lifecycle and visibility are not altered or inferred.
 raw[136]=0
 helper=ModelRecordBuilder(rom);memory=scene_memory(closed,rom);missing=[]
 @Read
 def read(_,address,target,size):
  try:C.memmove(target,memory.read(address,size),size);return 1
  except ValueError:missing.append((address,size));return 0
 state=C.create_string_buffer(closed.graph.context[:256],256);source=C.create_string_buffer(bytes(raw),164)
 xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16)
 if helper.lib.nfs_visibility_object_branch_prepare(state,source,encode_region(region),closed.graph.context[256:304],xyz,C.byref(branch),child)!=1 or branch.value!=0:raise ValueError('Unsupported external candidate branch')
 material=(C.c_uint32*4)()
 if hidden_depth:
  if not xyz[2]&0x80000000 or not struct.unpack_from('<H',raw,10)[0]&2:raise ValueError('Unverified hidden external material depth')
  helper.lib.nfs_visibility_object_material.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
  helper.lib.nfs_visibility_object_texture.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
  if not helper.lib.nfs_visibility_object_material(source,struct.unpack_from('<I',state.raw,36)[0],xyz[2],material) or material[1]!=0:raise ValueError('Invalid hidden external material selection')
  texture=(C.c_uint32*2)();asset=memory.read(material[0],32)
  if not helper.lib.nfs_visibility_object_texture(source,asset,None,struct.unpack_from('<I',state.raw,4)[0],material[1],texture) or texture[1]:raise ValueError('Invalid hidden external texture selection')
  material[2],material[3]=texture[0],texture[1]
 else:
  if helper.lib.nfs_visibility_object_material_plan(state,source,xyz,read,None,helper.reciprocal,material)!=1 or material[3]:raise ValueError(('Incomplete external material closure',missing))
 context=C.create_string_buffer(68)
 if helper.lib.nfs_visibility_object_model_plan(state,source,material,read,None,context)!=1:raise ValueError(('Incomplete external model closure',missing))
 blocks=model_record_blocks(context.raw,memory,matrix,closed.graph.context[304:368],tuple(region[1:5]),closed.graph.context[384:896])
 if missing:raise ValueError(('Incomplete external asset closure',missing))
 return blocks
