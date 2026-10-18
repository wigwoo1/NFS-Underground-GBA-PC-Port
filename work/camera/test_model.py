from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x03000000,0x10000),(0x02000000,0x40000),(0x08000000,0x800000)]:u.mem_map(address,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x71b0c+0x6000])
d=C.CDLL(str((root/'native_model.dll').resolve()))
d.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint32,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+0x6001*4])
def native(matrix,source,count,scale,x,y,original):
    mb=C.create_string_buffer(bytes(matrix));sb=C.create_string_buffer(bytes(source));dst=C.create_string_buffer(original)
    ok=d.nfs_model_project(mb,sb,count,scale,x,y,table,dst)
    return ok,dst.raw[:count*4]
r=random.Random(0x45e0);culls=0
for case in range(2000):
    count=r.randrange(0,65);matrix=struct.pack('<12i',*[r.randint(-16384,16384) for _ in range(9)],r.randint(-1000,1000),r.randint(-1000,1000),r.randint(-200,25000))
    source=struct.pack('<'+'h'*count*3,*[r.randint(-3000,3000) for _ in range(count*3)])
    # Explicit depth boundary coverage and zero-vertex behavior.
    if case<20:
        matrix=struct.pack('<12i',16384,0,0,0,16384,0,0,0,0,0,0,[-1,0,1,24576,24577][case%5])
    scale=r.randrange(1,65536);x=r.randint(-32768,32767);y=r.randint(-32768,32767);original=r.randbytes(count*4)
    context=bytearray(68);descriptor=bytearray(40);projection=bytearray(64)
    for offset,value in [(8,0x02002000),(12,0x02001000),(16,0x02004000),(48,0x02010000),(60,0x02003000),(64,scale)]:struct.pack_into('<I',context,offset,value)
    struct.pack_into('<H',descriptor,36,count);struct.pack_into('<hh',projection,8,x,y)
    for address,data in [(0x02000000,context),(0x02001000,descriptor),(0x02002000,projection),(0x02003000,matrix),(0x02004000,source),(0x02010000,original)]:
        if data:u.mem_write(address,bytes(data))
    for reg,value in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
    u.emu_start(0x030045e0,0x03007000,count=10000)
    ok,dest=native(matrix,source,count,scale,x,y,original)
    assert ok==u.reg_read(UC_ARM_REG_R0),(case,'return')
    assert dest==bytes(u.mem_read(0x02010000,count*4)),(case,'output')
    culls+=not ok
report={'result':'PASS','randomized_cases':2000,'culled_cases':culls,'scope':'Integer model transform/projection only; not integrated into player.'}
(root/'native-model-tests.json').write_text(json.dumps(report,indent=2));print(report)
