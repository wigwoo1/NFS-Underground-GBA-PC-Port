from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));loader=C.CDLL(str((p/'road-metadata-preview.dll').resolve())).nf_preview_metadata_component
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Meta(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t),('mode',C.c_uint)]
d.nf_scene_world_metadata_all.argtypes=[Section,C.POINTER(Meta),C.c_uint,C.POINTER(C.c_uint)];loader.argtypes=[C.POINTER(Meta)]+[C.c_void_p]*4
packet=(p/'road-camera-command-produced.packet').read_bytes();o,n=struct.unpack_from('<2I',packet,48);buf=C.create_string_buffer(packet[o:o+n]);items=(Meta*128)();count=C.c_uint();assert d.nf_scene_world_metadata_all(Section(C.addressof(buf),n),items,128,C.byref(count));roads=0
for item in items[:count.value]:
 if item.mode not in (9,10):continue
 a=C.create_string_buffer(288);c=C.create_string_buffer(56);present=C.c_uint();affine=C.c_uint();assert loader(C.byref(item),a,c,C.byref(present),C.byref(affine));payload=C.string_at(item.data,item.size);assert a.raw==payload[-288:] and c.raw==payload[-344:-288] and present.value==1 and affine.value==(item.mode==10)
 legacy=payload[:-344]+payload[-288:];owned=C.create_string_buffer(legacy);m=Meta(C.addressof(owned),len(legacy),6 if item.mode==10 else 5);assert loader(C.byref(m),a,c,C.byref(present),C.byref(affine));assert present.value==0 and c.raw==bytes(56)
 bad=bytearray(payload);struct.pack_into('<I',bad,len(bad)-344,2);owned=C.create_string_buffer(bytes(bad));m=Meta(C.addressof(owned),len(bad),item.mode);a=C.create_string_buffer(bytes([77])*288,288);c=C.create_string_buffer(bytes([77])*56,56);present=C.c_uint(77);affine=C.c_uint(77);assert not loader(C.byref(m),a,c,C.byref(present),C.byref(affine));assert a.raw==bytes([77])*288 and c.raw==bytes([77])*56 and present.value==affine.value==77;roads+=1
report=dict(result='PASS',camera_records=roads,legacy_records=roads,atomic_bad_version_rejections=roads,scope='Exact helper used by preview loading; GPU rendering and moving matrix interpolation not verified.')
(p/'road-metadata-preview-tests.json').write_text(json.dumps(report,indent=2));print(report)
