"""Original native visibility/material gates over captured ordinary source candidates."""
import runpy,ctypes as C,struct,json
v=runpy.run_path('work/camera/audit_multicar_source_identity.py');rom=v['rom']
from owned_closed_scene_memory import ClosedSceneMemory
from owned_ordinary_model_visits import ordinary_model_visits
lib=C.CDLL('work/camera/visibility-probe-wide.dll');Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32)
lib.nfs_visibility_object_branch_prepare.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
lib.nfs_visibility_object_material_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p]
lib.nfs_visibility_object_model_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);output=[]
for endpoint,scene in enumerate(v['scenes']):
 memory=ClosedSceneMemory(scene,rom);errors=[]
 @Read
 def read(_,address,target,size):
  try:C.memmove(target,memory.read(address,size),size);return 1
  except Exception as e:errors.append((address,size,str(e)));return 0
 queue=v['portal'].sample(endpoint);rows=[]
 for visit in ordinary_model_visits(scene,queue):
  state=C.create_string_buffer(scene.graph.context[:256],256);source=C.create_string_buffer(visit['source'],164);region=struct.pack('<8H',*queue[visit['ordinal']],65535);xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16)
  assert lib.nfs_visibility_object_branch_prepare(state,source,region,scene.graph.context[256:304],xyz,C.byref(branch),child)==1
  assert branch.value==0
  material=(C.c_uint32*4)();status=lib.nfs_visibility_object_material_plan(state,source,xyz,read,None,reciprocal,material)
  assert status>=0,(visit['object'],errors)
  context=C.create_string_buffer(68);ready=lib.nfs_visibility_object_model_plan(state,source,material,read,None,context) if status and material[3]==0 else 0
  assert ready>=0,(visit['object'],errors)
  model_context=list(struct.unpack('<17I',context.raw)) if ready else []
  assert not ready or model_context[3]==visit['dispatch']['descriptor']
  matrix_owned=True
  if ready:
   try:memory.read(model_context[15],48)
   except ValueError:matrix_owned=False
  rows.append(dict(matrix_owned=matrix_owned,ready=ready,model_context=model_context,object=visit['object'],ordinal=visit['ordinal'],xyz=list(xyz),visible=status,material=list(material)))
 output.append(rows)
assert [[x['object'] for x in rows if x['visible'] and x['material'][3]==0] for rows in output]==[[37,48,44,31,34,0],[37,48,44,31,34,0]],output
(v['folder']/'ordinary-native-visibility.json').write_text(json.dumps(output,indent=2))
print('PASS original owned native visibility admits six model candidates at both endpoints; later model culling remains to recover')




