"""Actual captured roads: validated bulk tail equals original full-scan getter."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Metadata(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t),('mode',C.c_uint)]
bulk=d.nf_scene_world_metadata_all;bulk.argtypes=[Section,C.POINTER(Metadata),C.c_uint,C.POINTER(C.c_uint)]
getter=d.nf_scene_world_road_attributes;getter.argtypes=[Section,C.c_uint,C.c_void_p]
packet=(p/'road-transition-live.packet').read_bytes();off,size=struct.unpack_from('<II',packet,48)
world=packet[off:off+size];buf=C.create_string_buffer(world);items=(Metadata*128)();count=C.c_uint()
assert bulk(Section(C.addressof(buf),size),items,128,C.byref(count))
roads=0;rejections=0
for i in range(count.value):
 m=items[i]
 if m.mode not in (5,6):continue
 original=C.create_string_buffer(288);assert getter(Section(C.addressof(buf),size),i,original)
 assert original.raw==C.string_at(m.data+m.size-288,288);roads+=1
 bad=bytearray(world);raw_offset=m.data-C.addressof(buf)+m.size-288
 struct.pack_into('<I',bad,raw_offset,0) # invalid raw count
 broken=C.create_string_buffer(bytes(bad));out=(Metadata*128)();C.memset(out,0xA5,C.sizeof(out));before=bytes(out);n=C.c_uint(999)
 assert not bulk(Section(C.addressof(broken),size),out,128,C.byref(n))
 assert bytes(out)==before and n.value==999;rejections+=1
assert roads
report=dict(result='PASS',captured_roads=roads,atomic_invalid_raw_rejections=rejections,scope='Actual retained packet: bulk raw copy equals original getter; malformed count rejected before consumer sees span. Does not establish whole-scene visual fidelity.')
(p/'live-bulk-road-attribute-tests.json').write_text(json.dumps(report,indent=2));print(report)
