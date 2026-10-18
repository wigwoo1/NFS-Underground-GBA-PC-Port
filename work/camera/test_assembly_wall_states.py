from pathlib import Path
import runpy,ctypes as C,struct,json
p=Path('work/camera');ns=runpy.run_path(str(p/'test_scene_assembly.py'));d=ns['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
d.nf_assembly_wall_states.argtypes=[P,U,P,Z,U]
d.nf_assembly_surface_indices.argtypes=[P,U,P,Z]
d.nf_scene_world_wall_states.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
d.nf_scene_world_indices.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z)]
reference=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes();model,mid,surfaces,order,table=ns['parts'](reference)
owner=d.nf_assembly_create();expected={};walls=[]
try:
 for index,(identity,asset,light) in enumerate(reversed(surfaces)):
  kind=struct.unpack_from('<I',identity)[0];_,w,h=struct.unpack_from('<3I',asset)
  if kind==2:
   lit=len(walls)%2;planes=17 if lit else 1
   light=struct.pack('<5I',1,0,0,w,h)+asset[-w*h*4:]*16 if lit else bytes(4)
   base=bytes(0 if j%7==0 else 2 for j in range(w*h))
   payload=base+b''.join(bytes(0 if v==0 else 1 if (j+level)%3==0 else 2 for j,v in enumerate(base)) for level in range(16)) if lit else base
   walls.append((identity,asset,light,payload,planes))
  else:payload=bytes([index+1])*(w*h);planes=0
  assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light)
  buf=C.create_string_buffer(payload)
  assert (d.nf_assembly_wall_states(owner,index,buf,len(payload),planes) if planes else d.nf_assembly_surface_indices(owner,index,buf,len(payload)))
  C.memset(buf,255,len(payload));expected[identity]=(payload,planes)
 assert len(walls)>=2
 assert ns['copied_call'](d.nf_assembly_model,owner,mid,model)
 meta=struct.unpack_from('<4I',reference,16);out=P();size=Z()
 assert d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size));d.nf_assembly_reset(owner)
 try:packet=C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
 wo,ws=struct.unpack_from('<2I',packet,48);io,_=struct.unpack_from('<2I',packet,84);wb=C.create_string_buffer(packet[wo:wo+ws]);section=Section(C.addressof(wb),ws)
 for index in range(len(surfaces)):
  identity=packet[io+8+index*20:io+28+index*20];payload,planes=expected[identity];ptr=P(123);length=Z(456);got=U(789)
  if planes:
   assert d.nf_scene_world_wall_states(section,index,C.byref(ptr),C.byref(length),C.byref(got));assert got.value==planes and C.string_at(ptr,length.value)==payload
   ptr=P(123);length=Z(456);assert not d.nf_scene_world_indices(section,index,C.byref(ptr),C.byref(length));assert (ptr.value,length.value)==(123,456)
  else:
   assert d.nf_scene_world_indices(section,index,C.byref(ptr),C.byref(length)) and C.string_at(ptr,length.value)==payload
   ptr=P(123);length=Z(456);assert not d.nf_scene_world_wall_states(section,index,C.byref(ptr),C.byref(length),C.byref(got));assert (ptr.value,length.value,got.value)==(123,456,789)
 identity,asset,light,payload,planes=next(x for x in walls if x[4]==17)
 bad=[]
 for offset,value in [(1,3),(1,1),(len(payload)//17,2)]:
  data=bytearray(payload);data[offset]=value;bad.append((bytes(data),17))
 for data,nplanes in bad+[(payload,16),(payload[:-1],17)]:
  assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light)
  buf=C.create_string_buffer(data);assert not d.nf_assembly_wall_states(owner,0,buf,len(data),nplanes)
  out=P(123);size=Z(456);assert not d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size));assert (out.value,size.value)==(123,456);d.nf_assembly_reset(owner)
finally:d.nf_assembly_destroy(owner)
report=dict(result='PASS',walls=len(walls),owned_classification_bytes=sum(len(v[0]) for v in expected.values() if v[1]),mixed_road_lit_unlit=True,reverse_identity_mapping=True,caller_mutation_reset_survival=True,atomic_poison_guards=5,scope='Prepared assembly; original command producer and live consumer pending.')
(p/'assembly-wall-states-tests.json').write_text(json.dumps(report,indent=2));print(report)
