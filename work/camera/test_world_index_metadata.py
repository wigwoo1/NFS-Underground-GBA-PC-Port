from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
a=d.nf_scene_world_attach_indices;a.argtypes=[Section,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
b=d.nf_scene_world_indices;b.argtypes=[Section,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
raw=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes();off,size=struct.unpack_from('<2I',raw,48);world=raw[off:off+size];n,w,h=struct.unpack_from('<3I',world,8);pixels=w*h
buf=C.create_string_buffer(world);indices=C.create_string_buffer(bytes(i%256 for i in range(pixels)));out=C.c_void_p();length=C.c_size_t()
assert a(Section(C.addressof(buf),len(world)),0,indices,pixels,C.byref(out),C.byref(length))
try:tagged=C.string_at(out,length.value)
finally:d.nf_scene_packet_free(out)
C.memset(indices,99,pixels);C.memset(buf,0,len(world));tb=C.create_string_buffer(tagged);borrow=C.c_void_p();count=C.c_size_t()
assert b(Section(C.addressof(tb),len(tagged)),0,C.byref(borrow),C.byref(count));assert count.value==pixels and C.string_at(borrow,pixels)==bytes(i%256 for i in range(pixels))
guards=0
for offset,value in [(len(world),0),(len(world)+4,129),(len(world)+8,2),(len(world)+12,pixels+1)]:
 broken=bytearray(tagged);struct.pack_into('<I',broken,offset,value);bb=C.create_string_buffer(bytes(broken));borrow=C.c_void_p(123);count=C.c_size_t(456)
 assert not b(Section(C.addressof(bb),len(broken)),0,C.byref(borrow),C.byref(count));assert (borrow.value,count.value)==(123,456);guards+=1
for broken in [tagged[:-1],tagged+b'X']:
 bb=C.create_string_buffer(broken);borrow=C.c_void_p(123);count=C.c_size_t(456);assert not b(Section(C.addressof(bb),len(broken)),0,C.byref(borrow),C.byref(count));assert (borrow.value,count.value)==(123,456);guards+=1
# Rebuild original full packet directory with annotated world; validate whole packet.
sections=[]
for i in range(5):
 o,z=struct.unpack_from('<2I',raw,36+i*12);sections.append(tagged if i==1 else raw[o:o+z])
packet=bytearray(raw[:96])
for i,s in enumerate(sections):
 packet.extend(bytes((-len(packet))%8));struct.pack_into('<2I',packet,36+i*12,len(packet),len(s));packet.extend(s)
struct.pack_into('<I',packet,8,len(packet));pb=C.create_string_buffer(bytes(packet));view=C.create_string_buffer(128);d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p];assert d.nf_scene_packet_view(pb,len(packet),view)
# Incrementally tag every surface and retain distinct payloads across replacements.
current=tagged;position=8;shapes=[]
for surface in range(struct.unpack_from('<I',world,4)[0]):
 corners,width,height=struct.unpack_from('<3I',world,position);shapes.append(width*height);position+=12+corners*40+width*height*4
for surface,pixels_i in enumerate(shapes):
 cb=C.create_string_buffer(current);payload=C.create_string_buffer(bytes([surface%256])*pixels_i);new=C.c_void_p();length=C.c_size_t()
 assert a(Section(C.addressof(cb),len(current)),surface,payload,pixels_i,C.byref(new),C.byref(length))
 try:current=C.string_at(new,length.value)
 finally:d.nf_scene_packet_free(new)
cb=C.create_string_buffer(current)
for surface,pixels_i in enumerate(shapes):
 borrow=C.c_void_p();count=C.c_size_t();assert b(Section(C.addressof(cb),len(current)),surface,C.byref(borrow),C.byref(count))
 assert count.value==pixels_i and C.string_at(borrow,pixels_i)==bytes([surface%256])*pixels_i
# Replace one surface and verify every other surface survives.
replacement=C.create_string_buffer(bytes([77])*shapes[0]);new=C.c_void_p();length=C.c_size_t()
assert a(Section(C.addressof(cb),len(current)),0,replacement,shapes[0],C.byref(new),C.byref(length))
try:
 for surface,pixels_i in enumerate(shapes):
  borrow=C.c_void_p();count=C.c_size_t();assert b(Section(new.value,length.value),surface,C.byref(borrow),C.byref(count))
  assert C.string_at(borrow,pixels_i)==bytes([77 if surface==0 else surface%256])*pixels_i
finally:d.nf_scene_packet_free(new)
report=dict(result='PASS',owned_world_indices=pixels,all_surfaces_tagged=len(shapes),distinct_surface_indices=sum(shapes),replacement_preserves_other_surfaces=True,atomic_malformed_rejections=guards,whole_packet_roundtrip=True,scope='Optional world metadata ownership/validation; producer and GPU rendering pending.')
(p/'world-index-metadata-tests.json').write_text(json.dumps(report,indent=2));print(report)
