import ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent
ns={};exec(compile((p/'test_scene_assembly.py').read_text().replace("scene_assembly.dll","visibility-probe-wide.dll"),str(p/'test_scene_assembly.py'),'exec'),ns)
d=ns['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint32
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
d.nf_assembly_wall_indices.argtypes=[P,U,P,P,Z,U]
d.nf_scene_world_wall_indices.argtypes=[Section,U,C.POINTER(P),C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
reference=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes()
model,mid,surfaces,order,table=ns['parts'](reference)
identity,asset,_=next(s for s in surfaces if struct.unpack_from('<I',s[0])[0]==2)
_,w,h=struct.unpack_from('<3I',asset);pixels=w*h;meta=struct.unpack_from('<4I',reference,16)
checks=[]
for planes in (1,17):
 owner=d.nf_assembly_create()
 try:
  light=bytes(4) if planes==1 else struct.pack('<5I',1,0,0,w,h)+asset[-pixels*4:]*16
  states=bytes(0 if i%7==0 else 2 for i in range(pixels))*planes
  indices=bytes(77 if state==2 else 0 for state in states)
  assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light)
  a=C.create_string_buffer(states);b=C.create_string_buffer(indices)
  assert d.nf_assembly_wall_indices(owner,0,a,b,len(states),planes)
  C.memset(a,255,len(states));C.memset(b,255,len(indices))
  assert ns['copied_call'](d.nf_assembly_model,owner,mid,model)
  out=P();size=Z();assert d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size))
  try:packet=C.string_at(out,size.value)
  finally:d.nf_scene_packet_free(out)
  d.nf_assembly_reset(owner)
  wo,ws=struct.unpack_from('<2I',packet,48);raw=C.create_string_buffer(packet[wo:wo+ws]);a=P();b=P();size=Z();n=U()
  assert d.nf_scene_world_wall_indices(Section(C.addressof(raw),ws),0,C.byref(a),C.byref(b),C.byref(size),C.byref(n))
  assert size.value==len(states) and n.value==planes and C.string_at(a,size.value)==states and C.string_at(b,size.value)==indices
  assert ns['copied_call'](d.nf_assembly_surface,owner,identity,asset,light)
  bad=bytearray(indices);bad[0]=1
  assert not d.nf_assembly_wall_indices(owner,0,states,bytes(bad),len(states),planes)
  out=P(123);size=Z(456);assert not d.nf_assembly_finish(owner,*meta,table,len(table),C.byref(out),C.byref(size)) and (out.value,size.value)==(123,456)
  checks.append(dict(planes=planes,paired_bytes_exact=len(states)*2,poison_reset_survives=True,invalid_poison_atomic=True))
 finally:d.nf_assembly_destroy(owner)
report=dict(result='PASS',checks=checks,scope='Actual retained wall geometry with synthetic output-index planes through complete assembly; bridgeemission/GPUpending.')
(p/'assembly-wall-indices-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
