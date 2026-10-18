"""Explicit original front64 difference, cutoff agreement and atomic outputs."""
from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Vertex(C.Structure):_fields_=[('p',Point),('u',C.c_double),('v',C.c_double)]
class Raw(C.Structure):_fields_=[('count',C.c_uint32),('shift',C.c_uint32),('height',C.c_uint32),('affine',C.c_uint32),('material',C.c_uint32),('animation',C.c_uint32),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
lib=C.CDLL(str((p/'road-corrected-clip-probe.dll').resolve()));base=lib.nf_corrected_clip_probe;continuous=lib.nf_continuous_clip_probe;base.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];continuous.argtypes=base.argtypes+[C.c_void_p]
ref=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));clip=ref.nfs_visibility_wall_clip;clip.argtypes=[C.c_void_p]*3+[C.c_int,C.c_uint,C.c_uint,C.c_void_p];project=ref.nfs_visibility_surface_vertices;project.argtypes=[C.c_void_p]*6+[C.c_size_t,C.c_void_p]
table=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes());cases=[]
for affine in (0,1):
 raw=Raw();raw.count=4;raw.shift=8;raw.height=128;raw.affine=affine
 for i,value in enumerate(((0,0),(16384,16384),(16384,0),(0,16384))):raw.attributes[i][:]=value
 for depth in (64,64.25,64.9999999,65,100):
  incoming=(Vertex*4)(*[Vertex(Point(x,y,z),0,0) for x,y,z in ((-10,-10,-700),(10,-10,depth),(10,10,500),(-10,10,500))]);old=(Vertex*64)();new=(Vertex*64)();a=C.c_uint();b=C.c_uint();adjusted=C.c_uint()
  assert base(incoming,4,old,C.byref(raw),table,C.byref(a)) and continuous(incoming,4,new,C.byref(raw),table,C.byref(b),C.byref(adjusted));assert a.value==b.value
  for i in range(a.value):assert bytes(old[i].p)==bytes(new[i].p)
  difference=max(abs(getattr(old[i],k)-getattr(new[i],k)) for i in range(a.value) for k in ('u','v'))
  assert adjusted.value==(1 if depth<65 else 0)
  if depth>=65:assert bytes(old)[:a.value*C.sizeof(Vertex)]==bytes(new)[:b.value*C.sizeof(Vertex)]
  if depth==64:
   scratch=bytearray(52);struct.pack_into('<2h',scratch,4,-700,64);edge=C.create_string_buffer(bytes(scratch));heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(0,0,16384,16384);stream=C.create_string_buffer(48);n=C.c_uint()
   assert clip(edge,heights,attrs,64,0,0,table)==1;params=(C.c_uint32*6)(1,0,0,8,128,affine);assert project(edge,heights,attrs,params,table,stream,48,C.byref(n))
   words=struct.unpack_from('<6i',stream.raw);q=65536 if affine else words[3];expected=[words[4]/q/128,words[5]/q/64]
   assert max(abs(getattr(old[1],k)-expected[i]) for i,k in enumerate(('u','v')))<1e-12
   assert new[1].u==new[2].u and new[1].v==new[2].v and difference>0
  cases.append(dict(affine=affine,front_depth=depth,adjustments=adjusted.value,maximum_original_policy_uv_difference=difference))
rejections=0
for field,value in (('count',3),('shift',11),('height',3),('affine',2)):
 invalid=Raw.from_buffer_copy(raw);setattr(invalid,field,value);out=(Vertex*64)();C.memset(out,0x5a,C.sizeof(out));before=bytes(out);n=C.c_uint(777);adjusted=C.c_uint(888)
 assert not continuous(incoming,4,out,C.byref(invalid),table,C.byref(n),C.byref(adjusted));assert bytes(out)==before and n.value==777 and adjusted.value==888;rejections+=1
report=dict(result='PASS',cases=cases,atomic_rejections=rejections,scope='Continuous presentation policy intentionally changes original biased front64 generated UV to the uncut corner; original-native mismatch quantified, not hidden. Geometry exact, unchanged original policy when front>=65, validated atomic failures. Not universal endpoint/raster fidelity or smooth60fps proof.')
(p/'road-continuous-uv-tests.json').write_text(json.dumps(report,indent=2));print(report)
