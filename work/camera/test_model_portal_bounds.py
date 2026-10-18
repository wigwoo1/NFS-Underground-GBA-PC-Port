"""Owned NFB2 model clipping metadata, legacy compatibility and atomic rejection."""
import ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Packet(C.Structure):_fields_=[('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('page',C.c_uint),('sections',Section*5)]
d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)];d.nf_scene_packet_model_bounds.argtypes=[C.POINTER(Packet),C.POINTER(C.c_void_p)]
checks=[]
for serial,right in ((858,18),(859,12),(860,5)):
 data=(p/f'visibility-original-{serial}.packet').read_bytes();owned=C.create_string_buffer(data);view=Packet();assert d.nf_scene_packet_view(owned,len(data),C.byref(view))
 bounds=C.c_void_p();assert d.nf_scene_packet_model_bounds(C.byref(view),C.byref(bounds));actual=C.string_at(bounds,32);assert struct.unpack_from('<4H',actual)==(0,right,0,158)
 checks.append(dict(serial=serial,tiny_car_bounds=list(struct.unpack_from('<4H',actual)),all_model_bounds=list(struct.unpack('<16H',actual))))
legacy=(p/'prototype-runs'/'threaded-route-22a8bcc2d9b1430798d0ceb163b79ea0-capture-01-native-scene.bin').read_bytes();view=Packet();owned=C.create_string_buffer(legacy);assert d.nf_scene_packet_view(owned,len(legacy),C.byref(view));ptr=C.c_void_p();assert not d.nf_scene_packet_model_bounds(C.byref(view),C.byref(ptr))
data=(p/'visibility-original-859.packet').read_bytes();tag,ids_offset,ids_size=struct.unpack_from('<3I',data,80);assert tag==5
count=struct.unpack_from('<I',data,ids_offset+4)[0];trailer=ids_offset+8+20*count;world=struct.unpack_from('<I',data,struct.unpack_from('<I',data,48)[0]+4)[0]
mutations=[]
for label,offset,fmt,value in [('model_right',trailer+16+world*8+2,'H',241),('model_reversed',trailer+16+world*8,'H',13),('trailer_count',trailer+4,'I',world),('trailer_tag',trailer,'I',0x3142464e)]:
 bad=bytearray(data);struct.pack_into('<'+fmt,bad,offset,value);owner=C.create_string_buffer(bytes(bad));view=Packet();C.memset(C.byref(view),0xa5,C.sizeof(view));before=bytes(view)
 assert not d.nf_scene_packet_view(owner,len(bad),C.byref(view));assert bytes(view)==before;mutations.append(label)
report=dict(result='PASS',source_model_bounds=checks,legacy_nfb1_accepted=True,invalid_nfb2_atomic_reject=mutations,scope='Owned packet source bounds and strict schema validation; native raster coverage comparison and live timings are separate tests.')
(p/'model-portal-bounds-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
