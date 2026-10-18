from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x62f700]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);u.mem_write(0x02001000,table)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_rect;fn.argtypes=[C.c_void_p]*5;rng=random.Random(2460);recip=C.create_string_buffer(table)
for case in range(1024):
 obj=bytearray(rng.randbytes(164));mat=rng.randbytes(32);size=struct.unpack_from('<h',obj,0x70)[0];p=(C.c_uint32*6)(rng.getrandbits(32),rng.getrandbits(32),rng.randrange(8192),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32));u.mem_write(0x02000400,mat)
 for off,val in [(8,p[2]),(12,p[1]),(16,p[0]),(24,p[3]),(28,p[5]),(32,p[4])]:u.mem_write(0x02018000+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R0,size&0xffffffff),(UC_ARM_REG_R4,0x02000400),(UC_ARM_REG_R5,0x02001000),(UC_ARM_REG_SP,0x02018000)]:u.reg_write(reg,val)
 u.emu_start(0x03002460,0x030024d8,count=100)
 out=(C.c_uint32*4)();assert fn(C.create_string_buffer(bytes(obj)),C.create_string_buffer(mat),p,recip,out)
 assert list(out)==[u.reg_read(reg) for reg in [UC_ARM_REG_LR,UC_ARM_REG_R5,UC_ARM_REG_R1,UC_ARM_REG_R0]],case
p[2]=8192;before=bytes(out);assert not fn(C.create_string_buffer(bytes(obj)),C.create_string_buffer(mat),p,recip,out) and bytes(out)==before
report=dict(result='PASS',original_ARM_rectangle_cases=1024,invalid_depth_atomic=True,scope='Alternate-path projected rectangle only; no live examples or rasterization verified.')
(root/'visibility-object-rect-tests.json').write_text(json.dumps(report,indent=2));print(report)
