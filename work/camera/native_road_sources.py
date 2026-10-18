"""Road source replay from raw world blocks; no saved projected-ring JSON input.
Scratch Q carries across draw invocations. Initial unresolved draws explicit.
"""
import struct,ctypes as C
from scene_batches import records
def road_sources(p):
 events=list(records(p/'motion-original-source-8750-8781.bin'));table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
 native=C.CDLL(str((p/'native-road-source-clipped.dll').resolve()))
 native.nf_road_scratch_create.restype=C.c_void_p;native.nf_road_scratch_destroy.argtypes=[C.c_void_p]
 native.nf_road_scratch_ring.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
 native.nf_road_scratch_commit.argtypes=[C.c_void_p,C.c_uint32,C.c_uint,C.c_void_p,C.c_uint]
 native.nf_road_source_clipped.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
 scratch=native.nf_road_scratch_create();assert scratch
 try:
  for draw in events:
   if draw['pc']!=0x030032f0:continue
   blocks={k:v[1] for k,v in draw['blocks'].items()};descriptor=draw['blocks'][4][0]
   count=struct.unpack_from('<H',blocks[4],2)[0];face=blocks[42] or bytes(20);offsets=b''.join(blocks[10+j] or bytes(32) for j in range(count))
   affine=struct.unpack('<2I',blocks[69])[0];base=draw['blocks'][7][0];bd=struct.unpack_from('<4H',blocks[1],226);first=struct.unpack_from('<H',blocks[1],242)[0]
   clipped=(C.c_double*768)();cn=C.c_uint();mask=C.c_uint64()
   assert native.nf_road_source_clipped(scratch,blocks[5],len(blocks[5]),offsets,len(offsets),face,blocks[8],count,affine,blocks[2],(C.c_uint16*4)(*bd),base,first,table,clipped,128,C.byref(cn),C.byref(mask))
   missing=[j for j in range(64) if mask.value&(1<<j)]
   checks.append(dict(clipped_ring=[list(clipped[j*6:j*6+6]) for j in range(cn.value)],bounds=list(bd),orientation=struct.unpack('<2I',blocks[69])[1],framebuffer=struct.unpack_from('<I',blocks[3])[0],material_hex=blocks[8].hex(),offsets=list(struct.unpack_from('<2h',blocks[9],4)),event=draw['id'],refresh=draw['frame'],source=descriptor,affine=affine,missing_initial_slots=missing,first=first))
 finally:native.nf_road_scratch_destroy(scratch)
 return checks
