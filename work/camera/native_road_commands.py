import ctypes as C,struct
from scene_batches import records
def road_commands(p):
 lib=C.CDLL(str((p/'native-road-source-runs.dll').resolve()));fn=lib.nf_road_source_runs
 fn.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint,C.c_void_p,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
 lib.nf_road_scratch_create.restype=C.c_void_p;lib.nf_road_scratch_destroy.argtypes=[C.c_void_p]
 handle=lib.nf_road_scratch_create();assert handle
 table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());result=[];fields=(0,1,2,5,6,7,8,9,10,11,14,15);index=0
 try:
  for event in records(p/'motion-original-source-8750-8781.bin'):
   if event['pc']!=0x030032f0:continue
   blocks={k:v[1] for k,v in event['blocks'].items()};n=struct.unpack_from('<H',blocks[4],2)[0]
   offsets=b''.join(blocks[10+j] or bytes(32) for j in range(n));affine,orientation=struct.unpack('<2I',blocks[69]);bounds=struct.unpack_from('<4H',blocks[1],226);first=struct.unpack_from('<H',blocks[1],242)[0]
   uv=struct.unpack_from('<2h',blocks[9],4);out=(C.c_uint32*(8192*17))();count=C.c_uint();missing=C.c_uint64()
   assert fn(handle,blocks[5],len(blocks[5]),offsets,len(offsets),blocks[42] or bytes(20),blocks[8],n,affine,blocks[2],(C.c_uint16*4)(*bounds),event['blocks'][7][0],first,table,struct.unpack_from('<I',blocks[3])[0],orientation,(C.c_uint32*2)(*uv),out,8192,C.byref(count),C.byref(missing))
   if index>=2:
    assert not missing.value
    for i in range(count.value):
     words=list(out[i*17:i*17+17]);r=words[:16];result.append(dict(refresh=event['frame'],event=event['id'],params=r,signature=[r[k] for k in fields]+[words[16]]))
   index+=1
 finally:lib.nf_road_scratch_destroy(handle)
 return result
