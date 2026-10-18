from pathlib import Path
import runpy,sys,ctypes as C,json,struct
p=Path('work/camera');sys.argv=['oracle','0.5'];ns=runpy.run_path(str(p/'test_classified_command_scene.py'));d=ns['d'];source=ns['ns'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
fn=d.nf_assembly_commands_road_camera_model_inputs;fn.argtypes=ns['args'];out=P(123);size=Z(456)
assert fn(source['commands'],source['command_count'].value,source['owned_ids'],None,.5,source['immutable_reader'],None,ns['palette'],None,source['model_inputs'][:48],ns['inputs'],None,*source['packet_header'][4:8],source['table'],C.byref(out),C.byref(size))
try:packet=C.string_at(out,size.value)
finally:d.nf_scene_packet_free(out)
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
o,n=struct.unpack_from('<2I',packet,48);world=C.create_string_buffer(packet[o:o+n]);section=Section(C.addressof(world),n);get=d.nf_scene_world_road_camera;get.argtypes=[Section,U,P]
roads=0
for index in range(struct.unpack_from('<I',packet,o+4)[0]):
 result=C.create_string_buffer(56)
 if get(section,index,result):
  version,address=struct.unpack_from('<2I',result.raw);assert version==1;expected=C.create_string_buffer(48);assert source['immutable_reader'](None,address,expected,48);assert result.raw[8:]==expected.raw;roads+=1
assert roads>0
(p/'road-camera-command-produced.packet').write_bytes(packet)
report=dict(result='PASS',camera_roads=roads,complete_packet_bytes=len(packet),owned_reader_matrix_bytes_exact=True,scope='Offline sampled command producer; live snapshot wrapper/preview/source renderer pending.')
(p/'road-camera-command-tests.json').write_text(json.dumps(report,indent=2));print(report)
