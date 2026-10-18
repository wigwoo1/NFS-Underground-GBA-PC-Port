"""Owned enriched command producer versus previous manual packet attachment."""
from pathlib import Path
import ctypes as C,json,struct,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['fixture','0.5'];fixture=runpy.run_path(str(p/'test_classified_command_scene.py'));ns=fixture['ns'];d=ns['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint;Read=ns['Read'];Palette=fixture['Palette'];Inputs=fixture['Inputs']
fn=d.nf_assembly_commands_road_attributes_model_inputs;fn.argtypes=fixture['args'];calls=[]
@Read
def reader(ctx,address,out,size):calls.append((address,size));return ns['immutable_reader'](ctx,address,out,size)
args=(ns['commands'],ns['command_count'].value,ns['owned_ids'],None,.5,reader,None,fixture['palette'],None,ns['model_inputs'][:48],fixture['inputs'],None,*ns['packet_header'][4:8],ns['table'])
out=P(123);size=Z(456);assert fn(*args,C.byref(out),C.byref(size))
try:packet=C.string_at(out,size.value)
finally:d.nf_scene_packet_free(out)
manual=(p/'road-attribute-corrected.packet').read_bytes();assert packet==manual,'Producer must equal independent manual enriched packet exactly'
(p/'road-attribute-produced.packet').write_bytes(packet)
def sections(raw):return [raw[o:o+n] for o,n in (struct.unpack_from('<2I',raw,36+i*12) for i in range(5))]
base=(p/'classified-command-scene.packet').read_bytes();a,b=sections(base),sections(packet)
for i in (0,2,3,4):assert a[i]==b[i]
world=a[1];cursor=8;count=struct.unpack_from('<I',world,4)[0]
for _ in range(count):corners,w,h=struct.unpack_from('<3I',world,cursor);cursor+=12+corners*40+w*h*4
assert a[1][:cursor]==b[1][:cursor],'Existing native geometry/UV/texture bytes unchanged'
# Repeat finish and exact result; no allocator-dependent metadata/padding.
out=P();size=Z();assert fn(*args,C.byref(out),C.byref(size))
try:assert C.string_at(out,size.value)==packet
finally:d.nf_scene_packet_free(out)
last=calls[-1]
@Read
def fail(ctx,address,out,size):
 if (address,size)==last:return 0
 return ns['immutable_reader'](ctx,address,out,size)
bad_args=list(args);bad_args[5]=fail;out=P(123);size=Z(456);assert not fn(*bad_args,C.byref(out),C.byref(size)) and (out.value,size.value)==(123,456)
report=dict(result='PASS',packet_bytes=len(packet),enriched_roads=10,manual_attachment_byte_exact=True,existing_sections_and_world_core_byte_exact=True,repeated_production_byte_exact=True,failed_read_atomic=True,scope='Explicit owned native-command enriched producer, one captured complete scene. Default producer unchanged. No live capture/renderer integration, motion or timing proof.')
(p/'road-attribute-producer-tests.json').write_text(json.dumps(report,indent=2));print(report)
