"""Owned affine road indices and strict packet consumer contracts."""
from pathlib import Path
import ctypes as C, struct, json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
attach=d.nf_scene_world_attach_road_mapping;attach.argtypes=[Section,U,P,Z,U,C.POINTER(P),C.POINTER(Z)]
get=d.nf_scene_world_road_mapping;get.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
old=d.nf_scene_world_indices;old.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z)]
wall=d.nf_scene_world_wall_states;wall.argtypes=get.argtypes
d.nf_scene_packet_free.argtypes=[P]
raw=(p/'classified-command-scene.packet').read_bytes();off,n=struct.unpack_from('<2I',raw,48);world=raw[off:off+n]
corners,width,height=struct.unpack_from('<3I',world,8);pixels=width*height
payload=bytes(i%256 for i in range(pixels));source=C.create_string_buffer(payload);buf=C.create_string_buffer(world)
out=P();size=Z();assert attach(Section(C.addressof(buf),n),0,source,pixels,1,C.byref(out),C.byref(size))
try:tagged=C.string_at(out,size.value)
finally:d.nf_scene_packet_free(out)
C.memset(source,99,pixels);C.memset(buf,0,n)
tb=C.create_string_buffer(tagged);sec=Section(C.addressof(tb),len(tagged));ptr=P();length=Z();mode=U()
assert get(sec,0,C.byref(ptr),C.byref(length),C.byref(mode)) and mode.value==1 and length.value==pixels and C.string_at(ptr,pixels)==payload
for reader in (old,wall):
 ptr=P(123);length=Z(456);mode=U(789)
 args=[sec,0,C.byref(ptr),C.byref(length)]+([C.byref(mode)] if reader==wall else [])
 assert not reader(*args) and (ptr.value,length.value,mode.value)==(123,456,789)
for affine in (2,0xffffffff):
 out=P(123);size=Z(456);assert not attach(sec,0,source,pixels,affine,C.byref(out),C.byref(size));assert (out.value,size.value)==(123,456)
# Validate affine metadata inside its complete captured packet, then reject a wall identity.
sections=[]
for i in range(5):
 o,z=struct.unpack_from('<2I',raw,36+i*12);sections.append(tagged if i==1 else raw[o:o+z])
def packet(parts):
 b=bytearray(raw[:96])
 for i,s in enumerate(parts):
  b.extend(bytes((-len(b))%8));struct.pack_into('<2I',b,36+i*12,len(b),len(s));b.extend(s)
 struct.pack_into('<I',b,8,len(b));return bytes(b)
view=d.nf_scene_packet_view;view.argtypes=[P,Z,P]
full=packet(sections);fb=C.create_string_buffer(full);v=C.create_string_buffer(128);assert view(fb,len(full),v)
wrong=list(sections);ident=bytearray(wrong[4]);struct.pack_into('<I',ident,8,2);wrong[4]=bytes(ident);bad=packet(wrong);bb=C.create_string_buffer(bad);sentinel=C.create_string_buffer(b'X'*128,128)
assert not view(bb,len(bad),sentinel) and sentinel.raw==b'X'*128
for broken in (tagged[:-1],tagged+b'X'):
 bb=C.create_string_buffer(broken);ptr=P(123);length=Z(456);mode=U(789)
 assert not get(Section(C.addressof(bb),len(broken)),0,C.byref(ptr),C.byref(length),C.byref(mode));assert (ptr.value,length.value,mode.value)==(123,456,789)
report=dict(result='PASS',affine_indices=pixels,owned_copy=True,complete_packet_valid=True,atomic_rejections=7,scope='Affine metadata packet contract only; production producer and GPU interpolation not yet integrated.')
(p/'road-mapping-metadata-tests.json').write_text(json.dumps(report,indent=2));print(report)
