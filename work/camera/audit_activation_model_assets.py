"""Original material/model planning for inactive source candidates."""
import runpy,ctypes as C,struct,json
from pathlib import Path
v=runpy.run_path('work/camera/test_inactive_scenery_visits.py');rom=v['rom'];scenes=v['scenes'];portal=v['portal']
from owned_closed_scene_memory import ClosedSceneMemory
from owned_ordinary_model_visits import ordinary_model_visits
lib=C.CDLL('work/camera/visibility-probe-wide.dll');Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32)
lib.nfs_visibility_object_branch_prepare.argtypes=[C.c_void_p]*7
lib.nfs_visibility_object_material_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
lib.nfs_visibility_object_model_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);results=[]
for endpoint,scene in enumerate(scenes):
 memory=ClosedSceneMemory(scene,rom);missing=[]
 @Read
 def read(_,address,target,n):
  try:C.memmove(target,memory.read(address,n),n);return 1
  except ValueError:missing.append((address,n));return 0
 queue=portal.sample(endpoint);items=[]
 for visit in ordinary_model_visits(scene,queue,True):
  if not 31<=visit['dispatch']['model']<=36:continue
  raw=bytearray(visit['source']);raw[136]=0 # Preparation only; original source remains unchanged.
  source=C.create_string_buffer(bytes(raw),164);state=C.create_string_buffer(scene.graph.context[:256],256)
  xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16);region=struct.pack('<8H',*queue[visit['ordinal']],65535)
  assert lib.nfs_visibility_object_branch_prepare(state,source,region,scene.graph.context[256:304],xyz,C.byref(branch),child)==1 and branch.value==0
  material=(C.c_uint32*4)();visible=lib.nfs_visibility_object_material_plan(state,source,xyz,read,None,reciprocal,material);assert visible==1 and material[3]==0
  context=C.create_string_buffer(68);assert lib.nfs_visibility_object_model_plan(state,source,material,read,None,context)==1,(visit['object'],missing)
  words=struct.unpack('<17I',context.raw);assert words[3]==visit['dispatch']['descriptor']
  texture_address=words[13];shift,height=struct.unpack_from('<2H',context.raw,56)
  texture=memory.read(texture_address,(1<<shift)*height)
  items.append(dict(object=visit['object'],allocated=visit['allocated'],descriptor=words[3],texture_address=texture_address,texture_bytes=len(texture),shift=shift,height=height,context=list(words)))
 assert not missing
 results.append(dict(endpoint=endpoint,items=items))
assert all(len(x['items'])==5 for x in results)
(v['folder']/'activation-model-assets.json').write_text(json.dumps(results,indent=2));print('PASS: five inactive and five active model/material/texture plans from owned source memory')
