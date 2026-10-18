from pathlib import Path
p=Path('work/camera/owned_model_record_builder.py');s=p.read_text();s=s.replace("return self._prepare(newer,new_queue,visit,False)\n def prepare_visit", "return self._prepare(newer,new_queue,visit,False,False)\n def prepare_visit")
s=s.replace('def _prepare(self,scene,queue,visit,require_chain):','def _prepare(self,scene,queue,visit,require_chain,require_visibility=True):')
needle="  if self.lib.nfs_visibility_object_material_plan(owned_state,source,xyz,read,None,self.reciprocal,material)!=1 or material[3]!=0:raise ValueError('Unverified scenery material')"
assert needle in s
s=s.replace(needle,'''  if require_visibility:
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
''');p.write_text(s)
