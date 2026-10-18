import ctypes as C,json,sys
from pathlib import Path
from native_scene_executor import Event
lib=C.CDLL(str(Path(sys.argv[1] if len(sys.argv)>1 else 'work/camera/native_scene_executor.dll').resolve()))
lib.nf_scene_create.argtypes=[C.c_void_p,C.c_size_t];lib.nf_scene_create.restype=C.c_void_p
lib.nf_scene_submit.argtypes=[C.c_void_p,C.POINTER(Event),C.c_uint]
lib.nf_scene_snapshot.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_uint64)]
lib.nf_scene_destroy.argtypes=[C.c_void_p]
lib.nf_scene_fork.argtypes=[C.c_void_p];lib.nf_scene_fork.restype=C.c_void_p
seed=(C.c_uint8*0x18000)(*([71]*0x18000));handle=lib.nf_scene_create(seed,len(seed));assert handle
out=(C.c_uint8*len(seed))();generation=C.c_uint64()
def snapshot():
 assert lib.nf_scene_snapshot(handle,out,len(out),C.byref(generation))
 return bytes(out),generation.value
try:
 seed[0]=99
 assert snapshot()[0][0]==71
 fill=(C.c_uint32*3)(0,0x12345678,32)
 e=Event(4,1,0,0,C.cast(fill,C.c_void_p),None,0,None,None)
 assert lib.nf_scene_submit(handle,C.byref(e),1)
 fill[1]=0
 first,g=snapshot();assert first[:32]==bytes.fromhex('78563412')*8 and g==1
 # Owned road texture range supplies native reads, without external callback.
 road=(C.c_uint32*17)(0,0,0,0,0,0x08000000,0x06000040,1,0,0,0,0,0,0,0,0,1)
 texture=(C.c_uint8*2)(0xcd,0xab)
 e=Event(1,1,0,0x08000000,C.cast(road,C.c_void_p),C.cast(texture,C.c_void_p),2,None,None)
 assert lib.nf_scene_submit(handle,C.byref(e),1)
 texture[0]=0
 second,g=snapshot();assert g==2 and second[:32]==first[:32]
 assert second[64:66]==bytes.fromhex('cdab') and second[304:306]==bytes.fromhex('cdab')
 e.texture_size=1
 assert not lib.nf_scene_submit(handle,C.byref(e),1)
 assert snapshot()==(second,2)
 bad=Event(99,0,0,0,None,None,0,None,None)
 assert not lib.nf_scene_submit(handle,C.byref(bad),1) and snapshot()==(second,2)
 branch=lib.nf_scene_fork(handle);assert branch
 try:
  fill[0]=0x14000;fill[1]=0xaabbccdd
  update=Event(4,1,0,0,C.cast(fill,C.c_void_p),None,0,None,None)
  assert lib.nf_scene_submit(branch,C.byref(update),1)
  branchout=(C.c_uint8*len(seed))();branchgen=C.c_uint64()
  assert lib.nf_scene_snapshot(branch,branchout,len(branchout),C.byref(branchgen))
  assert bytes(branchout[0x14000:0x14020])==bytes.fromhex('ddccbbaa')*8 and branchgen.value==3
  assert snapshot()==(second,2)
 finally:lib.nf_scene_destroy(branch)
 r=dict(result='PASS',native_fork_isolation=True,seed_copied=True,persistent_multiple_submissions=True,source_mutation_does_not_change_committed_scene=True,owned_road_reader_and_doubled_row=True,failed_submit_keeps_scene_and_generation=True)
 Path('work/camera/native-scene-ownership-tests.json').write_text(json.dumps(r,indent=2));print(r)
finally:lib.nf_scene_destroy(handle)
