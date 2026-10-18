from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
raw=next((p/'prototype-runs').glob('racing-motion-a88232*-complete-stable-bundle.bin')).read_bytes() if False else (p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin').read_bytes()
at=raw.find(b'NSP1');assert at>=0;packet=raw[at:];offset,size=struct.unpack_from('<2I',packet,48);world=packet[offset:offset+size];storage=C.create_string_buffer(world);section=Section(C.addressof(storage),len(world))
attach=d.nf_scene_world_attach_road_camera;attach.argtypes=[Section,C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
attrs=d.nf_scene_world_road_attributes;attrs.argtypes=[Section,C.c_uint,C.c_void_p]
mapfn=d.nf_scene_world_road_mapping;mapfn.argtypes=[Section,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t),C.POINTER(C.c_uint)]
get=d.nf_scene_world_road_camera;get.argtypes=[Section,C.c_uint,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
e=json.loads((p/'stable-original-road-source.json').read_text())['roads'][0];camera=struct.pack('<2I',1,e['blocks']['2']['address'])+bytes.fromhex(e['blocks']['2']['hex']);cases=0
for index in (0,1,2):
 a=C.create_string_buffer(288);assert attrs(section,index,a);ptr=C.c_void_p();n=C.c_size_t();aff=C.c_uint();assert mapfn(section,index,C.byref(ptr),C.byref(n),C.byref(aff));indices=C.string_at(ptr,n.value);out=C.c_void_p(123);length=C.c_size_t(456)
 assert attach(section,index,indices,len(indices),a,camera,C.byref(out),C.byref(length))
 try:
  enriched=Section(out,length.value);copy=C.create_string_buffer(56);assert get(enriched,index,copy) and copy.raw==camera
  aa=C.create_string_buffer(288);assert attrs(enriched,index,aa) and aa.raw==a.raw
  assert mapfn(enriched,index,C.byref(ptr),C.byref(n),C.byref(aff)) and C.string_at(ptr,n.value)==indices
 finally:d.nf_scene_packet_free(out)
 bad=bytearray(camera);struct.pack_into('<I',bad,0,2);out=C.c_void_p(123);length=C.c_size_t(456);assert not attach(section,index,indices,len(indices),a,bytes(bad),C.byref(out),C.byref(length));assert (out.value,length.value)==(123,456)
 copy=C.create_string_buffer(bytes([77])*56,56);assert not get(section,index,copy) and copy.raw==bytes([77])*56;cases+=1
report=dict(result='PASS',roads=cases,old_attribute_and_mapping_accessors_exact=True,unsupported_version_atomic=True,legacy_camera_absence_atomic=True,scope='Optional modes9/10 packet attachment/accessors only; assembly producer and renderer not yet wired.')
(p/'road-camera-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)
