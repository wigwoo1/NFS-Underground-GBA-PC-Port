"""Synthetic original clipping/projection differential for source correction."""
from pathlib import Path
import ctypes as C,random,struct,json
p=Path('work/camera');original=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));candidate=C.CDLL(str((p/'road-near-attributes.dll').resolve())).nf_road_near_attributes
P=C.c_void_p;candidate.argtypes=[C.c_double,C.c_double,P,C.c_uint,C.c_uint,C.c_uint,C.c_int,P,P]
clip=original.nfs_visibility_wall_clip;clip.argtypes=[P,P,P,C.c_int,C.c_uint,C.c_uint,P]
project=original.nfs_visibility_surface_vertices;project.argtypes=[P,P,P,P,P,P,C.c_size_t,P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
rng=random.Random(94721);cases=0
for affine in (0,1):
 for order in (0,1):
  for trial in range(400):
   behind=rng.randrange(-14000,64);front=rng.randrange(64,14000);z0,z1=(behind,front) if order==0 else (front,behind)
   shift=rng.randrange(1,11);height=2*rng.randrange(1,513);raw=[rng.randrange(-32768,32768) for _ in range(4)]
   scratch=bytearray(52);struct.pack_into('<2h',scratch,4,z0,z1);edge=C.create_string_buffer(bytes(scratch));heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(*(v&0xffffffff for v in raw))
   assert clip(edge,heights,attrs,64,0,0,recip)==1
   params=(C.c_uint32*6)(1,0,0,shift,height,affine);stream=C.create_string_buffer(48);count=C.c_uint()
   assert project(edge,heights,attrs,params,recip,stream,48,C.byref(count))
   words=struct.unpack_from('<6i',stream.raw);q=65536 if affine else words[3];expected=[words[4]/q/((1<<shift)*.5),words[5]/q/(height*.5)]
   out=(C.c_double*2)();source=(C.c_int32*4)(*raw)
   assert candidate(z0,z1,source,shift,height,affine,64,recip,out)
   assert max(abs(out[k]-expected[k]) for k in (0,1))<1e-12,(affine,order,trial,list(out),expected)
   cases+=1
source=(C.c_int32*4)(0,1,2,3);rejections=0
for z0,z1,shift,height,near in ((65,66,8,128,64),(-5,-1,8,128,64),(float('nan'),100,8,128,64),(-1,100,11,128,64),(-1,100,8,3,64),(-1,100,8,128,0),(-32768,32767,8,128,64)):
 out=(C.c_double*2)(123,456);assert not candidate(z0,z1,source,shift,height,0,near,recip,out) and list(out)==[123,456];rejections+=1
report=dict(result='PASS',cases=cases,affine_cases=800,perspective_cases=800,atomic_rejections=rejections,scope='Candidate integer endpoints versus original native near clipping and projection across both directions and affine/perspective modes. Native reference independently verified against ARM previously; not GPU/fullscene or live integration.')
(p/'road-near-attribute-modes-tests.json').write_text(json.dumps(report,indent=2));print(report)
