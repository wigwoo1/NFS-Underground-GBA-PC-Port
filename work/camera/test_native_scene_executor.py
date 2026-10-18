import ctypes as C,json
from pathlib import Path
from native_scene_executor import Event,execute
vram=(C.c_uint8*0x18000)(*([71]*0x18000));before=bytes(vram)
fill=(C.c_uint32*3)(0,0x12345678,33)
copy=(C.c_uint32*5)(64,0,2,32,32)
source=(C.c_uint8*64)(*range(64))
block=(C.c_uint32*2)(0x14000,33)
def event(kind,commands,source=None,size=0):
 return Event(kind,1,0,0,C.cast(commands,C.c_void_p),C.cast(source,C.c_void_p) if source is not None else None,size,None,None)
events=(Event*3)(event(4,fill),event(5,copy,source,64),event(6,block,source,64))
assert execute(events,3,vram,len(vram),None)
assert bytes(vram[:32])==bytes.fromhex('78563412')*8 and vram[32]==71
assert bytes(vram[64:128])==bytes(range(64))
assert bytes(vram[0x14000:0x14020])==bytes(range(32)) and vram[0x14020]==71
C.memmove(vram,before,len(vram));sentinel=C.c_uint(12345)
invalid=(C.c_uint32*2)(0x17ff0,32)
failed=(Event*4)(*events,event(6,invalid,source,64))
assert not execute(failed,4,vram,len(vram),C.byref(sentinel))
assert bytes(vram)==before and sentinel.value==12345
r=dict(result='PASS',ordered_fill_background_sprite_copy=True,original_32byte_rounding=True,late_copy_failure_rolls_back_entire_batch=True)
Path('work/camera/native-scene-memory-event-tests.json').write_text(json.dumps(r,indent=2));print(r)
