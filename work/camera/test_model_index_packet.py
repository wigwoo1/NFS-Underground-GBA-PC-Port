from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
P=C.c_void_p;Z=C.c_size_t
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
class Packet(C.Structure):_fields_=[('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('page',C.c_uint32),('section',Section*5)]
d.nf_scene_packet_view.argtypes=[P,Z,P];d.nf_scene_packet_model.argtypes=[P,C.c_uint32,P]
d.nf_scene_model_attach_indices.argtypes=[Section,P,Z,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_model_indices.argtypes=[Section,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_free.argtypes=[P];d.nf_scene_packet_build.argtypes=[P,C.POINTER(P),C.POINTER(Z)]
blob=(p/'live-first-multimodel.packet').read_bytes();packet=Packet();assert d.nf_scene_packet_view(blob,len(blob),C.byref(packet))
model=Section();assert d.nf_scene_packet_model(C.byref(packet),0,C.byref(model))
original=C.string_at(model.data,model.size);width,height=struct.unpack_from('<2I',original,16);pixels=width*height
source=C.create_string_buffer(bytes(i%256 for i in range(pixels)),pixels);expected=source.raw;owned=P();size=Z()
assert d.nf_scene_model_attach_indices(model,source,pixels,C.byref(owned),C.byref(size))
try:
 C.memset(source,0xff,pixels);tagged=Section(owned,size.value);indices=P();length=Z()
 assert d.nf_scene_model_indices(tagged,C.byref(indices),C.byref(length)) and length.value==pixels and C.string_at(indices,pixels)==expected
 assert C.string_at(owned,model.size)==original
 # Validate roundtrip by reusing source packet and replacing its NML1 directory.
 old=C.string_at(packet.section[0].data,packet.section[0].size);count=struct.unpack_from('<I',old,4)[0]
 assets=[C.string_at(owned,size.value)]
 for i in range(1,count):
  off,n=struct.unpack_from('<2I',old,8+i*8);assets.append(old[off:off+n])
 section=bytearray(8+8*count);struct.pack_into('<2I',section,0,0x314c4d4e,count)
 for i,asset in enumerate(assets):
  section.extend(bytes((-len(section))%8));struct.pack_into('<2I',section,8+i*8,len(section),len(asset));section.extend(asset)
 buffer=C.create_string_buffer(bytes(section));packet.section[0]=Section(C.addressof(buffer),len(section));out=P();outsize=Z()
 assert d.nf_scene_packet_build(C.byref(packet),C.byref(out),C.byref(outsize))
 try:
  view=Packet();assert d.nf_scene_packet_view(out,outsize.value,C.byref(view));asset=Section();assert d.nf_scene_packet_model(C.byref(view),0,C.byref(asset));assert d.nf_scene_model_indices(asset,C.byref(indices),C.byref(length)) and C.string_at(indices,pixels)==expected
 finally:d.nf_scene_packet_free(out)
 bad_cases=[];raw=C.string_at(owned,size.value)
 for offset,value in [(model.size,0),(model.size+4,width+1),(model.size+8,height+1),(model.size+12,1)]:
  bad=bytearray(raw);struct.pack_into('<I',bad,offset,value);bad_cases.append(bytes(bad))
 bad_cases.extend([raw[:-1],raw+b'X'])
 for bad in bad_cases:
  data=C.create_string_buffer(bad);indices=P(123);length=Z(456)
  assert not d.nf_scene_model_indices(Section(C.addressof(data),len(bad)),C.byref(indices),C.byref(length)) and (indices.value,length.value)==(123,456)
finally:d.nf_scene_packet_free(owned)
report=dict(result='PASS',indices_owned=pixels,packet_models=count,malformed_atomic_rejections=len(bad_cases),scope='Versioned NZI1 model index trailer and multi-model packet roundtrip; indices are synthetic diagnostic data, renderer explicitly rejects pending shader integration.')
(p/'model-index-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)
