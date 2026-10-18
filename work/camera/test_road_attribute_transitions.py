"""Source UV policy at uncut/near-clipped transitions, without GPU raster."""
from pathlib import Path
import ctypes as C,json,struct,random,math
p=Path('work/camera');lib=C.CDLL(str((p/'road-near-attributes.dll').resolve()));ref=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));P=C.c_void_p
vertex=lib.nf_road_vertex_attributes;vertex.argtypes=[C.c_double,P,C.c_uint,C.c_uint,C.c_uint,P,P]
near=lib.nf_road_near_attributes;near.argtypes=[C.c_double,C.c_double,P,C.c_uint,C.c_uint,C.c_uint,C.c_int,P,P]
project=ref.nfs_visibility_surface_vertices;project.argtypes=[P,P,P,P,P,P,C.c_size_t,P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
rng=random.Random(39103);cases=limits=depth_boundaries=0;max_limit=old_gap=0
for affine in (0,1):
 for trial in range(800):
  shift=rng.randrange(1,11);height=2*rng.randrange(1,513);depth=rng.randrange(64,32000);source=[rng.randrange(-16384,32768) for _ in range(4)]
  attrs=(C.c_int32*2)(*source[:2]);out=(C.c_double*2)()
  assert vertex(depth,attrs,shift,height,affine,recip,out)
  scratch=bytearray(52);struct.pack_into('<2h',scratch,4,depth,depth);heights=(C.c_uint32*4)();raw=(C.c_uint32*4)(*(x&0xffffffff for x in source[:2]*2));params=(C.c_uint32*6)(1,0,0,shift,height,affine);stream=C.create_string_buffer(48);count=C.c_uint()
  assert project(bytes(scratch),heights,raw,params,recip,stream,48,C.byref(count));words=struct.unpack_from('<6i',stream.raw);q=65536 if affine else words[3];expected=[words[4]/q/((1<<shift)*.5),words[5]/q/(height*.5)]
  assert max(abs(out[k]-expected[k]) for k in (0,1))<1e-12;cases+=1
  values=[]
  for z in (depth-1e-7,depth+1e-7):
   result=(C.c_double*2)();assert vertex(z,attrs,shift,height,affine,recip,result);values.append(list(result))
  assert max(abs(values[0][k]-values[1][k]) for k in (0,1))<1e-7;depth_boundaries+=1
  # Both ordered source-edge directions approach the same original corner
  # UV as the moving behind vertex reaches depth64. Other vertex stays front.
  front=rng.randrange(65,16000)
  for order in (0,1):
   raw=(C.c_int32*4)(*(source if order==0 else source[2:]+source[:2]));zs=(64-1e-7,front) if order==0 else (front,64-1e-7)
   clipped=(C.c_double*2)();boundary=(C.c_double*2)();uncut=(C.c_double*2)()
   assert near(*zs,raw,shift,height,affine,64,recip,clipped)
   assert vertex(64,attrs,shift,height,affine,recip,boundary) and vertex(64+1e-7,attrs,shift,height,affine,recip,uncut)
   error=max(abs(clipped[k]-uncut[k]) for k in (0,1));max_limit=max(max_limit,error);assert error<1e-6
   old_gap=max(old_gap,max(abs(boundary[k]-source[k]/16384) for k in (0,1)));limits+=1
report=dict(result='PASS',original_uncut_vertex_cases=cases,depth_cell_continuity_checks=depth_boundaries,near_plane_attribute_limit_checks=limits,maximum_normalized_limit_difference=max_limit,maximum_uncorrected_source_uv_gap=old_gap,scope='Candidate matches original native uncut vertex attributes at integer depths and approaches same corrected vertex UV from both near-clipped edge directions. Epsilon limits with stationary front vertex; no topology/raster/fullscene/live verification. Original span texture subdivision remains separate.')
(p/'road-attribute-transition-tests.json').write_text(json.dumps(report,indent=2));print(report)
