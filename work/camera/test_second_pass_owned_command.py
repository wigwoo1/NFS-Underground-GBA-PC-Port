"""Second-pass owned command assets from captured original road sources."""
import runpy,ctypes as C,json
from pathlib import Path
p=Path(__file__).resolve().parent;v=runpy.run_path(str(p/'test_road_second_layer_geometry.py'));globals().update({k:v[k] for k in ['d','Read','read','state','descriptor','source','overrides','asset','out','regs','get','w','h']});U=C.c_uint32;P=C.c_void_p
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
c=Command();c.head[0]=1;c.head[5]=descriptor;c.head[8]=1;C.memmove(c.state,source[:256],256);overrides[state]=bytes(256)
d.nf_scene_command_road_indices_owned.argtypes=[P,Read,P,P,P,P];ptr=P();width=U();height=U();assert d.nf_scene_command_road_indices_owned(C.byref(c),read,None,C.byref(ptr),C.byref(width),C.byref(height))
try:indices=C.string_at(ptr,width.value*height.value)
finally:d.nf_surface_free(ptr)
packed=get(w(source,344),width.value*height.value*2);assert indices==b''.join(packed[y*width.value*2:y*width.value*2+width.value] for y in range(height.value))
d.nf_extract_scene_command.argtypes=[P,Read,P,P,P,P,P,P];palette=(C.c_uint8*512)();ptr=P();size=C.c_size_t();stage=U(99);assert d.nf_extract_scene_command(C.byref(c),read,None,palette,None,C.byref(ptr),C.byref(size),C.byref(stage))
try:assert C.string_at(ptr,size.value)==asset and stage.value==0
finally:d.nf_surface_free(ptr)
plan=json.loads((out/'road-material-layer-test.json').read_text())['second'];c.head[9]=plan[0];c.head[10]=plan[2];c.head[11]=plan[3];c.head[12]=plan[4]
d.nf_scene_command_road_attributes_owned.argtypes=[P,Read,P,P];attrs=(C.c_uint8*288)();assert d.nf_scene_command_road_attributes_owned(C.byref(c),read,None,attrs)
import struct
raw=bytes(attrs);assert struct.unpack_from('<6I',raw)==(4,plan[3],plan[4],0,plan[0],plan[1]);assert struct.unpack_from('<2i',raw,24)==struct.unpack_from('<2h',source,356)
for i in range(4):
 vertex=get(w(source,16)+(h(source,256)+i)*68,68);assert raw[32+i*8:40+i*8]==vertex[32:40]
c.head[11]+=1;sentinel=(C.c_uint8*288)(*([165]*288));assert not d.nf_scene_command_road_attributes_owned(C.byref(c),read,None,sentinel) and bytes(sentinel)==bytes([165])*288;c.head[11]-=1
for bad in [2,0xffffffff]:
 c.head[8]=bad;ptr=P(123);width=U(456);height=U(789);assert not d.nf_scene_command_road_indices_owned(C.byref(c),read,None,C.byref(ptr),C.byref(width),C.byref(height)) and (ptr.value,width.value,height.value)==(123,456,789)
(out/'second-pass-owned-command-test.json').write_text(json.dumps(dict(result='PASS',checks=['secondpass indices exact original packed texture row layout','owned command state survives external state replacement','owned candidate worldgeometry/UV/fixturepalette bytes exact direct layer extractor','owned secondary raw UV policy matches captured source and animation','mismatched command material atomic rejection','invalid secondpass atomic rejection'],scope='Owned assets component; source attributes/full visibility packet and GPU not yet verified.'),indent=2));print('PASS owned secondary assets',len(indices),'indices')
