from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
class Metadata(C.Structure):_fields_=[('data',P),('size',Z),('mode',U)]
f=d.nf_scene_world_metadata_all;f.argtypes=[Section,C.POINTER(Metadata),U,C.POINTER(U)]
r=d.nf_scene_world_indices;r.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z)]
w=d.nf_scene_world_wall_states;w.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
mapping=d.nf_scene_world_road_mapping;mapping.argtypes=w.argtypes
raw=(p/'classified-command-scene.packet').read_bytes();o,n=struct.unpack_from('<2I',raw,48);world=raw[o:o+n];buf=C.create_string_buffer(world);section=Section(C.addressof(buf),n);items=(Metadata*128)();count=U()
assert f(section,items,128,C.byref(count))
for i in range(count.value):
 ptr=P();size=Z();planes=U();m=items[i]
 if m.mode==1:assert r(section,i,C.byref(ptr),C.byref(size))
 elif m.mode==4:assert mapping(section,i,C.byref(ptr),C.byref(size),C.byref(planes)) and planes.value==1
 elif m.mode in (2,3):assert w(section,i,C.byref(ptr),C.byref(size),C.byref(planes)) and planes.value==(17 if m.mode==3 else 1)
 else:continue
 assert (m.data,m.size)==(ptr.value,size.value)
original=bytes(items);bad=bytearray(world);j=next(i for i in range(count.value) if items[i].mode in (2,3));bad[items[j].data-C.addressof(buf)]=3;broken=C.create_string_buffer(bytes(bad));outcount=U(999)
for sec,capacity in [(section,count.value-1),(Section(C.addressof(broken),n),128),(Section(C.addressof(buf),n-1),128)]:
 assert not f(sec,items,capacity,C.byref(outcount));assert bytes(items)==original and outcount.value==999
report=dict(result='PASS',surfaces=count.value,bulk_borrows_match_single_getters=True,atomic_rejections=3,scope='One complete classified world bulk decoder; insufficient capacity, invalid state, truncation preserve outputs.')
(p/'world-metadata-bulk-tests.json').write_text(json.dumps(report,indent=2));print(report)
