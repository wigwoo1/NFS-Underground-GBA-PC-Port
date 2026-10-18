"""Reconstruct scenery matrices from raw source angles even before slot activation."""
import runpy,ctypes as C,struct,json
from pathlib import Path
v=runpy.run_path('work/camera/audit_model_population_transition.py')['v'];rom=v['rom']
from owned_scene_bundle import chunks
from owned_motion_pairs import records
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(_,address,target,size):
 offset=address-0x08000000
 if not 0<=offset<=len(rom)-size:return 0
 C.memmove(target,rom[offset:offset+size],size);return 1
lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nf_object_projection_matrix;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p];out=[]
for endpoint,scene in enumerate(v['scenes']):
 source={}
 for h,raw in chunks(scene.objects,'graph_objects'):
  for i in range(h[5]):source[struct.unpack_from('<I',raw,128+i*168)[0]]=raw[132+i*168:296+i*168]
 modelbase=struct.unpack_from('<I',scene.graph.context,124)[0];models=[r for r in records(v['frames'][endpoint])['records'] if r['kind']==3]
 for index in (31,34,37,44,48):
  obj=source[index];matrix=(C.c_int32*12)();assert fn(scene.graph.context[256:304],obj,matrix,read,None)
  descriptor=modelbase+(struct.unpack_from('<h',obj,54)[0]-1)*40;offset=descriptor-0x08000000;matches=[r for r in models if bytes(r['blocks'][1])==rom[offset:offset+40]]
  if endpoint==1:assert len(matches)==1
  actual=list(struct.unpack('<12i',matches[0]['blocks'][2])) if matches else None
  out.append(dict(endpoint=endpoint,object=index,slot=obj[136],matrix=list(matrix),actual_matrix=actual,exact_record_match=bool(matches) and bytes(matrix)==bytes(matches[0]['blocks'][2])))
(v['folder']/'source-scenery-matrices.json').write_text(json.dumps(out,indent=2));print([(x['object'],x['exact_record_match'],[a-b for a,b in zip(x['actual_matrix'],x['matrix'])]) for x in out if x['endpoint']==1])


