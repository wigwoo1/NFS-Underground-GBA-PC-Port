from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
a=d.nf_scene_world_attach_wall_states;a.argtypes=[Section,U,P,Z,U,C.POINTER(P),C.POINTER(Z)]
b=d.nf_scene_world_wall_states;b.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
road=d.nf_scene_world_attach_indices;road.argtypes=[Section,U,P,Z,C.POINTER(P),C.POINTER(Z)]
getroad=d.nf_scene_world_indices;getroad.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_free.argtypes=[P]
world=struct.pack('<2I',0x31444652,2)+2*(struct.pack('<3I',3,4,1)+bytes(120)+bytes(16))
states=bytes([0,2,2,2])+b''.join(bytes([0,1 if level%2 else 2,2,1]) for level in range(16))
def attach(raw,index,payload,planes=None):
 buf=C.create_string_buffer(raw);data=C.create_string_buffer(payload);out=P();size=Z()
 args=[Section(C.addressof(buf),len(raw)),index,data,len(payload)]+([] if planes is None else [planes])+[C.byref(out),C.byref(size)]
 assert (road if planes is None else a)(*args)
 try:return C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
tagged=attach(world,1,states,17);tagged=attach(tagged,0,bytes([0,1,2,255]))
buf=C.create_string_buffer(tagged);ptr=P();size=Z();planes=U()
assert b(Section(C.addressof(buf),len(tagged)),1,C.byref(ptr),C.byref(size),C.byref(planes))
assert (size.value,planes.value)==(68,17) and C.string_at(ptr,68)==states
ptr=P(123);size=Z(456)
assert not getroad(Section(C.addressof(buf),len(tagged)),1,C.byref(ptr),C.byref(size))
assert (ptr.value,size.value)==(123,456)
assert getroad(Section(C.addressof(buf),len(tagged)),0,C.byref(ptr),C.byref(size)) and C.string_at(ptr,4)==bytes([0,1,2,255])
base=attach(tagged,1,bytes([0,2,2,2]),1);assert base[:len(world)]==world
bad=[]
for offset,value in ((0,1),(4,2),(5,0),(6,3)):
 broken=bytearray(states);broken[offset]=value;bad.append(bytes(broken))
for payload,planes_in in [(x,17) for x in bad]+[(states[:-1],17),(states,16)]:
 raw=C.create_string_buffer(world);data=C.create_string_buffer(payload);out=P(123);size=Z(456)
 assert not a(Section(C.addressof(raw),len(world)),1,data,len(payload),planes_in,C.byref(out),C.byref(size))
 assert (out.value,size.value)==(123,456)
report=dict(result='PASS',mixed_road_wall_metadata=True,exact_wall_classifications=68,base_replacement_preserves_road=True,atomic_invalid_rejections=6,scope='World trailer ownership and classification consistency; full packet identity/lighting cross-check and assembly/live consumers pending')
fixture=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes()
offset,length=struct.unpack_from('<2I',fixture,36);model=fixture[offset:offset+length]
lighting=struct.pack('<3I',0x314c464e,2,0)+struct.pack('<5I',1,0,0,4,1)+bytes(256)+bytes(131072)
identities=struct.pack('<2I',0x3149464e,3)+struct.pack('<15I',1,0,10,0,0,2,0,20,0,0,3,0,30,0,0)
def packet(world_data,light=lighting,ids=identities):
 sections=[model,world_data,struct.pack('<5I',0x314f464e,3,0,1,0xffffffff),light,ids]
 raw=bytearray(fixture[:96])
 for i,s in enumerate(sections):
  raw.extend(bytes((-len(raw))%8));struct.pack_into('<2I',raw,36+i*12,len(raw),len(s));raw.extend(s)
 struct.pack_into('<I',raw,8,len(raw));return bytes(raw)
view=d.nf_scene_packet_view;view.argtypes=[P,Z,P]
def valid(raw,expected):
 buf=C.create_string_buffer(raw);out=C.create_string_buffer(bytes([77])*128,128)
 assert bool(view(buf,len(raw),out))==expected
 if not expected:assert out.raw==bytes([77])*128
valid(packet(tagged),True)
unlit=struct.pack('<4I',0x314c464e,2,0,0)+bytes(131072)
valid(packet(base,unlit),True)
wrong_id=bytearray(identities);struct.pack_into('<I',wrong_id,28,1)
valid(packet(tagged,ids=bytes(wrong_id)),False)
valid(packet(tagged,unlit),False)
valid(packet(base),False)
report.update(whole_packet_valid_modes=2,whole_packet_atomic_cross_rejections=3,scope='World trailer plus full packet identity/lighting cross-validation; assembly and live GPU consumer pending')
(p/'wall-packet-states-tests.json').write_text(json.dumps(report,indent=2));print(report)
