from pathlib import Path
import ctypes as C, struct, json
root=Path('work/camera'); d=C.CDLL(str((root/'scene_assembly.dll').resolve()))
P=C.c_void_p; Z=C.c_size_t; U=C.c_uint32
class Section(C.Structure): _fields_=[('data',P),('size',Z)]
class Packet(C.Structure): _fields_=[('serial',U),('begin',U),('end',U),('page',U),('section',Section*5)]
d.nf_assembly_create.restype=P
for name in ['reset','destroy']: getattr(d,'nf_assembly_'+name).argtypes=[P]
d.nf_assembly_multimodel.argtypes=[P,C.c_int]
d.nf_assembly_model.argtypes=[P,P,P,Z]
d.nf_assembly_surface.argtypes=[P,P,P,Z,P,Z]
d.nf_assembly_finish.argtypes=[P,U,U,U,U,P,Z,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_view.argtypes=[P,Z,C.POINTER(Packet)]
d.nf_scene_packet_model_count.argtypes=[C.POINTER(Packet)]
d.nf_scene_packet_model.argtypes=[C.POINTER(Packet),U,C.POINTER(Section)]
d.nf_scene_packet_free.argtypes=[P]
d.nf_scene_packet_with_bounds.argtypes=[P,Z,C.c_double,P,U,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_bounds.argtypes=[C.POINTER(Packet),C.POINTER(C.c_double),C.POINTER(P)]
reference=next((root/'packet-sequence').glob('scene-*.packet')).read_bytes()
sections=[]
for i in range(5):
 off,n=struct.unpack_from('<2I',reference,36+i*12); sections.append(reference[off:off+n])
model,world,order,lighting,identities=sections
n,w,h=struct.unpack_from('<3I',world,8); surface=world[8:20+n*40+w*h*4]
lit=struct.unpack_from('<I',lighting,8)[0]; light=lighting[8:8+(20+w*h*64 if lit else 4)]
pos=8
for _ in range(struct.unpack_from('<I',world,4)[0]):
 vertices,width,height=struct.unpack_from('<3I',world,pos); pos+=12+vertices*40+width*height*4
lp=8; wp=8
for _ in range(struct.unpack_from('<I',world,4)[0]):
 vertices,width,height=struct.unpack_from('<3I',world,wp); wp+=12+vertices*40+width*height*4
 enabled=struct.unpack_from('<I',lighting,lp)[0]; lp+=20+width*height*64 if enabled else 4
table=lighting[lp:]; mid=identities[-20:]; sid=identities[8:28]
def append_model(owner,index):
 asset=bytearray(model); struct.pack_into('<d',asset,104,index*123.25)
 identity=bytearray(mid); struct.pack_into('<I',identity,8,0x02000000+index*164)
 a=C.create_string_buffer(bytes(asset)); b=C.create_string_buffer(bytes(identity))
 ok=d.nf_assembly_model(owner,b,a,len(asset)); C.memset(a,0xCD,len(a)); C.memset(b,0xCD,len(b)); return ok,bytes(asset)
def view(raw):
 storage=C.create_string_buffer(raw); packet=Packet(); assert d.nf_scene_packet_view(storage,len(raw),C.byref(packet)); return storage,packet
owner=d.nf_assembly_create(); assert owner
corruptions=0; checked=[]
try:
 for count in [2,3,16]:
  d.nf_assembly_reset(owner); assert d.nf_assembly_multimodel(owner,1)
  expected=[]; commands=[]
  for i in range(count):
   ok,asset=append_model(owner,i); assert ok; expected.append(asset); commands.append(0xffffffff-i)
   if i==0:
    assert d.nf_assembly_surface(owner,sid,surface,len(surface),light,len(light)); commands.append(0)
  assert not d.nf_assembly_multimodel(owner,0)
  out=P(); size=Z(); assert d.nf_assembly_finish(owner,123,100,104,0,table,len(table),C.byref(out),C.byref(size))
  raw=C.string_at(out,size.value); d.nf_scene_packet_free(out); d.nf_assembly_reset(owner)
  storage,packet=view(raw); assert struct.unpack_from('<I',raw,4)[0]==2
  assert d.nf_scene_packet_model_count(C.byref(packet))==count
  for i,asset in enumerate(expected):
   item=Section(); assert d.nf_scene_packet_model(C.byref(packet),i,C.byref(item)); assert C.string_at(item.data,item.size)==asset
  item=Section(123,456); assert not d.nf_scene_packet_model(C.byref(packet),count,C.byref(item)); assert (item.data,item.size)==(123,456)
  command_bytes=C.string_at(packet.section[2].data,packet.section[2].size)
  assert list(struct.unpack_from(f'<{count+1}I',command_bytes,8))==commands
  ids=C.string_at(packet.section[4].data,packet.section[4].size)
  for i in range(count): assert struct.unpack_from('<I',ids,8+20*(i+1)+8)[0]==0x02000000+i*164
  bounds=(C.c_uint16*4)(0,240,0,160); bounded=P(); bounded_size=Z()
  assert d.nf_scene_packet_with_bounds(storage,len(raw),0.375,bounds,1,C.byref(bounded),C.byref(bounded_size))
  bounded_raw=C.string_at(bounded,bounded_size.value); d.nf_scene_packet_free(bounded)
  bounded_storage,bounded_packet=view(bounded_raw); alpha=C.c_double(); bounds_ptr=P()
  assert d.nf_scene_packet_bounds(C.byref(bounded_packet),C.byref(alpha),C.byref(bounds_ptr))
  assert alpha.value==0.375 and C.string_at(bounds_ptr,8)==bytes(bounds)
  for i,asset in enumerate(expected):
   item=Section(); assert d.nf_scene_packet_model(C.byref(bounded_packet),i,C.byref(item)); assert C.string_at(item.data,item.size)==asset
  model_offset=struct.unpack_from('<I',raw,36)[0]; order_offset=struct.unpack_from('<I',raw,60)[0]
  changes=[(4,1),(model_offset+4,17),(model_offset+8,0),(model_offset+12,159),(order_offset+8,0xffffffff-16),(order_offset+12,0xffffffff)]
  for offset,value in changes:
   bad=bytearray(raw); struct.pack_into('<I',bad,offset,value); buf=C.create_string_buffer(bytes(bad)); result=Packet(); C.memset(C.byref(result),0xA5,C.sizeof(result)); before=bytes(result)
   assert not d.nf_scene_packet_view(buf,len(bad),C.byref(result)); assert bytes(result)==before; corruptions+=1
  checked.append(count)
 # Opt-in survives reset and the seventeenth model poisons publication atomically.
 for i in range(16): assert append_model(owner,i)[0]
 assert not append_model(owner,16)[0]
 out=P(123); size=Z(456); assert not d.nf_assembly_finish(owner,123,100,104,0,table,len(table),C.byref(out),C.byref(size)); assert (out.value,size.value)==(123,456)
 report={'result':'PASS','model_counts':checked,'distinct_poses_identities_and_draw_order':True,'source_and_packet_ownership':True,'bounds_preserve_all_models':True,'atomic_malformed_packet_rejections':corruptions,'capacity_failure_atomic':True,'scope':'Prepared component snapshot ownership and parsing only; live producer, paired poses and renderer not yet integrated.'}
 (root/'multimodel-assembly-tests.json').write_text(json.dumps(report,indent=2)); print(report)
finally: d.nf_assembly_destroy(owner)
