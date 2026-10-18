from pathlib import Path
import runpy,ctypes as C,struct,json
p=Path('work/camera');ns=runpy.run_path(str(p/'test_scene_assembly.py'));d=ns['d'];P=C.c_void_p;Z=C.c_size_t
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
d.nf_assembly_surface_indices.argtypes=[P,C.c_uint,P,Z];d.nf_scene_world_indices.argtypes=[Section,C.c_uint,C.POINTER(P),C.POINTER(Z)]
reference=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes();model,mid,surfaces,order,table=ns['parts'](reference)
owner=d.nf_assembly_create();expected={};payloads=[]
try:
 # Append reverse order, including walls before roads; metadata must follow identities.
 for index,(identity,asset,light) in enumerate(reversed(surfaces)):
  assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light)
  if struct.unpack_from('<I',identity)[0]==1:
   _,w,h=struct.unpack_from('<3I',asset);payload=bytes([(index+1)%256])*(w*h);buf=C.create_string_buffer(payload)
   assert d.nf_assembly_surface_indices(owner,index,buf,len(payload));C.memset(buf,0,len(payload));expected[identity]=payload
 assert len(expected)>1;assert ns['copied_call'](d.nf_assembly_model,owner,mid,model)
 out=P();size=Z();meta=struct.unpack_from('<4I',reference,16);assert d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size))
 d.nf_assembly_reset(owner)
 try:packet=C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
 world_off,world_size=struct.unpack_from('<2I',packet,48);id_off,id_size=struct.unpack_from('<2I',packet,84);wb=C.create_string_buffer(packet[world_off:world_off+world_size]);count=struct.unpack_from('<I',packet,world_off+4)[0]
 for index in range(count):
  identity=packet[id_off+8+index*20:id_off+28+index*20];ptr=P(123);n=Z(456);present=d.nf_scene_world_indices(Section(C.addressof(wb),world_size),index,C.byref(ptr),C.byref(n))
  if identity in expected:assert present and C.string_at(ptr,n.value)==expected[identity]
  else:assert not present and (ptr.value,n.value)==(123,456)
 # Byte-for-byte comparison to the previous repeated-attachment serializer.
 world=packet[world_off:world_off+world_size];base=8
 for wi in range(count):
  corners,width,height=struct.unpack_from('<3I',world,base);base+=12+corners*40+width*height*4
 rebuilt=world[:base];attach=d.nf_scene_world_attach_indices;attach.argtypes=[Section,C.c_uint,P,Z,C.POINTER(P),C.POINTER(Z)]
 for wi in range(count):
  identity=packet[id_off+8+wi*20:id_off+28+wi*20]
  if identity not in expected:continue
  src=C.create_string_buffer(rebuilt);data=C.create_string_buffer(expected[identity]);owned=P();length=Z()
  assert attach(Section(C.addressof(src),len(rebuilt)),wi,data,len(expected[identity]),C.byref(owned),C.byref(length))
  try:rebuilt=C.string_at(owned,length.value)
  finally:d.nf_scene_packet_free(owned)
 assert rebuilt==world,'bulk serialization changed indexed world bytes'
 # Invalid size poisons scene and keeps finish outputs untouched.
 identity,asset,light=next(s for s in surfaces if struct.unpack_from('<I',s[0])[0]==1)
 assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light);bad=C.create_string_buffer(b'X');assert not d.nf_assembly_surface_indices(owner,0,bad,1)
 out=P(123);size=Z(456);assert not d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size));assert (out.value,size.value)==(123,456)
finally:d.nf_assembly_destroy(owner)
report=dict(result='PASS',indexed_roads=len(expected),owned_index_bytes=sum(map(len,expected.values())),reverse_append_identity_mapping=True,bulk_world_serializer_byte_identical=True,caller_mutation_and_reset_survival=True,invalid_metadata_poison_rejected=True,scope='Prepared native assembly owns road indices and maps metadata through world reorder; command producer/live integration pending.')
(p/'assembly-road-indices-tests.json').write_text(json.dumps(report,indent=2));print(report)
