"""Owned assembler produces camera-bearing complete packets."""
from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');exec(compile((p/'test_road_camera_packet.py').read_text(),'packet_setup','exec'),globals())
P=C.c_void_p;Z=C.c_size_t
d.nf_assembly_create.restype=P;d.nf_assembly_destroy.argtypes=[P]
d.nf_assembly_surface.argtypes=[P,P,P,Z,P,Z];d.nf_assembly_surface_indices.argtypes=[P,C.c_uint,P,Z];d.nf_assembly_road_mapping.argtypes=[P,C.c_uint,C.c_uint];d.nf_assembly_road_attributes.argtypes=[P,C.c_uint,P];d.nf_assembly_road_camera.argtypes=[P,C.c_uint,P];d.nf_assembly_model.argtypes=[P,P,P,Z];d.nf_assembly_finish.argtypes=[P,C.c_uint,C.c_uint,C.c_uint,C.c_uint,P,Z,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_world_surface.argtypes=[Section,C.c_uint,C.POINTER(Section)]
sections=[packet[o:o+n] for o,n in (struct.unpack_from('<2I',packet,36+k*12) for k in range(5))];model,_,_,lighting,identity=sections;world_count=struct.unpack_from('<I',world,4)[0];mid=identity[8+world_count*20:28+world_count*20];table=lighting[-131072:];checked=0
for index in (0,1,2):
 assembly=d.nf_assembly_create();assert assembly;surface=Section();assert d.nf_scene_world_surface(section,index,C.byref(surface));asset=C.string_at(surface.data,surface.size);id=identity[8+index*20:28+index*20];a=C.create_string_buffer(288);assert attrs(section,index,a);ptr=P();n=Z();aff=C.c_uint();assert mapfn(section,index,C.byref(ptr),C.byref(n),C.byref(aff));indices=C.string_at(ptr,n.value)
 try:
  assert d.nf_assembly_surface(assembly,id,asset,len(asset),bytes(4),4)
  assert d.nf_assembly_surface_indices(assembly,0,indices,len(indices));assert d.nf_assembly_road_mapping(assembly,0,aff.value);assert d.nf_assembly_road_attributes(assembly,0,a);assert d.nf_assembly_road_camera(assembly,0,camera)
  assert d.nf_assembly_model(assembly,mid,model,len(model));out=P();n=Z();assert d.nf_assembly_finish(assembly,137,8775,8779,1,table,len(table),C.byref(out),C.byref(n))
  try:
   produced=C.string_at(out,n.value);wo,wn=struct.unpack_from('<2I',produced,48);w=C.create_string_buffer(produced[wo:wo+wn]);result=C.create_string_buffer(56);assert get(Section(C.addressof(w),wn),0,result) and result.raw==camera;checked+=1
  finally:d.nf_scene_packet_free(out)
 finally:d.nf_assembly_destroy(assembly)
report=dict(result='PASS',complete_assembled_camera_packets=checked,scope='Assembler API and complete packet validation; optional live command producer/preview consumption pending.')
(p/'road-camera-assembly-tests.json').write_text(json.dumps(report,indent=2));print(report)
