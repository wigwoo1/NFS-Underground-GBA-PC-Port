"""Complete captured-command classified producer differential (offline)."""
from pathlib import Path
import ctypes as C,struct,json,runpy,sys
alpha=sys.argv[1] if len(sys.argv)>1 else '0.5';assert alpha in ('0.25','0.5','0.75')
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['test_sampled_object_dispatch.py',alpha,'motion','road-full']
ns=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=ns['d'];P=C.c_void_p;U=C.c_uint;Z=C.c_size_t;Read=ns['Read']
Palette=C.CFUNCTYPE(C.c_int,P,U,P,Read,P,P,P);Inputs=C.CFUNCTYPE(C.c_int,P,U,P,P,P,P)
@Palette
def palette(user,ordinal,command,read,context,rotation,out):C.memmove(out,ns['model_inputs'][48:],512);return 1
@Inputs
def inputs(user,ordinal,command,identity,rotation,out):C.memmove(rotation,ns['model_inputs'][:48],48);C.memmove(out,ns['model_inputs'][48:],512);return 1
args=[P,U,P,P,C.c_double,Read,P,Palette,P,P,Inputs,P,U,U,U,U,P,C.POINTER(P),C.POINTER(Z)]
def build(name,reader):
 fn=getattr(d,name);fn.argtypes=args;out=P();size=Z()
 assert fn(ns['commands'],ns['command_count'].value,ns['owned_ids'],None,float(alpha),reader,None,palette,None,ns['model_inputs'][:48],inputs,None,*ns['packet_header'][4:8],ns['table'],C.byref(out),C.byref(size))
 try:return C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
base=build('nf_assembly_commands_indexed_world_model_inputs',ns['immutable_reader']);packet=build('nf_assembly_commands_classified_world_model_inputs',ns['immutable_reader'])
(p/'classified-command-scene.packet').write_bytes(packet)
(p/'indexed-command-scene.packet').write_bytes(base)
def sections(raw):return [raw[o:o+n] for o,n in (struct.unpack_from('<2I',raw,36+i*12) for i in range(5))]
a=sections(base);b=sections(packet)
for i in (0,2,3,4):assert a[i]==b[i],i
world=b[1];offset=8;count=struct.unpack_from('<I',world,4)[0]
for _ in range(count):n,w,h=struct.unpack_from('<3I',world,offset);offset+=12+n*40+w*h*4
assert a[1][:offset]==world[:offset]
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
get=d.nf_scene_world_wall_states;get.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
extract=d.nf_scene_command_wall_states_owned;extract.argtypes=[P,Read,P,C.POINTER(P),C.POINTER(U),C.POINTER(U),C.POINTER(U)]
wb=C.create_string_buffer(world);walls=total=lit=0
mapping=d.nf_scene_world_road_mapping;mapping.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
affine_roads=perspective_roads=0
for wi in range(count):
 identity=b[4][8+wi*20:28+wi*20]
 if struct.unpack_from('<I',identity)[0]==1:
  ordinal=next(i for i in range(ns['command_count'].value) if bytes(ns['owned_ids'])[i*20:i*20+20]==identity)
  ptr=P();size=Z();flag=U();assert mapping(Section(C.addressof(wb),len(world)),wi,C.byref(ptr),C.byref(size),C.byref(flag))
  assert flag.value==ns['commands'][ordinal].xyz[1]
  affine_roads+=flag.value;perspective_roads+=1-flag.value
 if struct.unpack_from('<I',identity)[0]!=2:continue
 ordinal=next(i for i in range(ns['command_count'].value) if bytes(ns['owned_ids'])[i*20:i*20+20]==identity)
 command=ns['commands'][ordinal];expected=P();w=U();h=U();planes=U();ptr=P();size=Z();got=U()
 assert extract(C.byref(command),ns['immutable_reader'],None,C.byref(expected),C.byref(w),C.byref(h),C.byref(planes))
 try:
  assert get(Section(C.addressof(wb),len(world)),wi,C.byref(ptr),C.byref(size),C.byref(got))
  assert got.value==planes.value and size.value==w.value*h.value*planes.value
  assert C.string_at(ptr,size.value)==C.string_at(expected,size.value);total+=size.value;walls+=1;lit+=planes.value==17
 finally:d.nf_surface_free(expected)
assert walls
assert affine_roads and perspective_roads
fn=d.nf_assembly_commands_classified_world_model_inputs;out=P(123);size=Z(456)
assert not fn(ns['commands'],ns['command_count'].value,ns['owned_ids'],None,float(alpha),ns['unavailable_reader'],None,palette,None,ns['model_inputs'][:48],inputs,None,*ns['packet_header'][4:8],ns['table'],C.byref(out),C.byref(size))
assert (out.value,size.value)==(123,456)
report=dict(result='PASS',sample_alpha=float(alpha),captured_commands=ns['command_count'].value,walls=walls,lit_walls=lit,exact_classification_bytes=total,geometry_model_order_lighting_identity_unchanged=True,unavailable_reader_atomic=True,scope='One captured sampled scene complete mode7 command producer; offline, no live GPU/timing proof.')
(p/f'classified-command-scene-{alpha}-tests.json').write_text(json.dumps(report,indent=2));
(p/'classified-command-scene-tests.json').write_text(json.dumps(report,indent=2));print(report)


