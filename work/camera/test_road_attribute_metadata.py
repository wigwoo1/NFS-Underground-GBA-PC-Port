"""Captured owned source UV packet round-trip and malformed metadata guards."""
from pathlib import Path
import ctypes as C,json,struct,sys,runpy
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full'];n=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=n['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
class Attributes(C.Structure):_fields_=[('count',U),('shift',U),('stored_height',U),('affine',U),('material',U),('animation',U),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
extract=d.nf_scene_command_road_attributes_owned;extract.argtypes=[P,n['Read'],P,P]
attach=d.nf_scene_world_attach_road_attributes;attach.argtypes=[Section,U,P,Z,P,C.POINTER(P),C.POINTER(Z)]
borrow=d.nf_scene_world_road_attributes;borrow.argtypes=[Section,U,P]
mapping=d.nf_scene_world_road_mapping;mapping.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
legacy=d.nf_scene_world_indices;legacy.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z)]
view=d.nf_scene_packet_view;view.argtypes=[P,Z,P];d.nf_scene_packet_free.argtypes=[P]
raw=(p/'classified-command-scene.packet').read_bytes();sections=[]
for i in range(5):
 off,size=struct.unpack_from('<2I',raw,36+i*12);sections.append(raw[off:off+size])
world=sections[1];source=struct.unpack_from('<I',sections[4],16)[0];command=next(c for c in n['commands'] if c.kind==1 and c.source==source)
attrs=Attributes();assert extract(C.byref(command),n['immutable_reader'],None,C.byref(attrs))
count,width,height=struct.unpack_from('<3I',world,8);assert attrs.count==count
indices=bytes(i%256 for i in range(width*height));cases=rejects=0
for affine in (0,1):
 attrs.affine=affine;wb=C.create_string_buffer(world);ib=C.create_string_buffer(indices);owned=P();length=Z()
 assert attach(Section(C.addressof(wb),len(world)),0,ib,len(indices),C.byref(attrs),C.byref(owned),C.byref(length))
 tagged=C.string_at(owned,length.value);d.nf_scene_packet_free(owned)
 C.memset(wb,0,len(world));C.memset(ib,99,len(indices))
 tb=C.create_string_buffer(tagged);sec=Section(C.addressof(tb),len(tagged));copy=Attributes()
 assert borrow(sec,0,C.byref(copy)) and bytes(copy)==bytes(attrs)
 ptr=P();size=Z();flag=U();assert mapping(sec,0,C.byref(ptr),C.byref(size),C.byref(flag)) and size.value==len(indices) and flag.value==affine and C.string_at(ptr,size.value)==indices
 # Returned attribute struct remains owned after packet storage mutation.
 saved=bytes(copy);C.memset(tb,0,len(tagged));assert bytes(copy)==saved
 tb=C.create_string_buffer(tagged);sec=Section(C.addressof(tb),len(tagged));ptr=P(123);size=Z(456)
 assert not legacy(sec,0,C.byref(ptr),C.byref(size)) and (ptr.value,size.value)==(123,456);rejects+=1
 parts=list(sections);parts[1]=tagged
 def packet(parts):
  data=bytearray(raw[:96])
  for i,part in enumerate(parts):
   data.extend(bytes((-len(data))%8));struct.pack_into('<2I',data,36+i*12,len(data),len(part));data.extend(part)
  struct.pack_into('<I',data,8,len(data));return bytes(data)
 full=packet(parts);(p/f'road-attributes-mode-{affine}.packet').write_bytes(full);fb=C.create_string_buffer(full);pv=C.create_string_buffer(128);assert view(fb,len(full),pv)
 # Locate owned attributes by mapped texture span, without native struct pointers.
 ptr=P();size=Z();flag=U();assert mapping(sec,0,C.byref(ptr),C.byref(size),C.byref(flag));offset=ptr.value-C.addressof(tb)+size.value
 corrupt=[]
 for field,value in ((0,count+1),(4,11),(8,height*2+2),(12,1-affine),(16,0),(20,0),(24,40000),(32,attrs.attributes[0][0]+1)):
  bad=bytearray(tagged);struct.pack_into('<I',bad,offset+field,value&0xffffffff);corrupt.append(bytes(bad))
 if count<32:
  bad=bytearray(tagged);struct.pack_into('<I',bad,offset+32+count*8,1);corrupt.append(bytes(bad))
 corrupt.extend((tagged[:-1],tagged+b'X'))
 for broken in corrupt:
  bb=C.create_string_buffer(broken);sentinel=C.create_string_buffer(b'X'*288,288)
  assert not borrow(Section(C.addressof(bb),len(broken)),0,sentinel) and sentinel.raw==b'X'*288
  parts[1]=broken;full_bad=packet(parts);bad_buf=C.create_string_buffer(full_bad);out=C.create_string_buffer(b'X'*128,128)
  assert not view(bad_buf,len(full_bad),out) and out.raw==b'X'*128;rejects+=1
 cases+=1
report=dict(result='PASS',captured_road_modes=cases,metadata_bytes=288,malformed_atomic_rejections=rejects,owned_copy=True,complete_packet_valid=True,source_uv_crosscheck=True,scope='Modes5/6 retain raw source attributes alongside owned indices and validate count/dimensions/mapping/animation offsets against native surface UVs. Legacy accessor rejects unsupported enriched modes. Current renderer rejects these modes until explicit integration; no live producer or scene-pair correction integration yet.')
(p/'road-attribute-metadata-tests.json').write_text(json.dumps(report,indent=2));print(report)
