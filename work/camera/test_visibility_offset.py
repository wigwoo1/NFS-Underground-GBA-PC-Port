from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(address,size)
u.mem_write(0x08000000,rom)
assert struct.unpack_from('<3I',rom,0x615f08)==(8,0,80)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_offset
fn.argtypes=[C.c_void_p,C.c_void_p];rng=random.Random(0x6dec0)
for i in range(1000):
    matrix=[rng.getrandbits(32) if i%2 else rng.randrange(-16384,16385)&0xffffffff for _ in range(12)]
    u.mem_write(0x02001000,struct.pack('<12I',*matrix))
    for reg,value in [(UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,0x08615f08),(UC_ARM_REG_R2,0x02002000),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,value)
    u.emu_start(0x0806dec1,0x03006000,count=200)
    assert u.reg_read(UC_ARM_REG_PC)==0x03006000
    out=(C.c_uint32*3)();assert fn((C.c_uint32*12)(*matrix),out)
    assert bytes(out)==bytes(u.mem_read(0x02002000,12)),i
out=(C.c_uint32*3)(1,2,3)
assert not fn(None,out) and list(out)==[1,2,3]
report=dict(result='PASS',original_Thumb_cases=1000,full_width_wrap_cases=500,normal_fixed14_cases=500,invalid_input_preserves_output=True,
 scope='Visibility seed affine transform with original integer arithmetic. Not a reconstruction of continuous camera matrices.')
(root/'visibility-offset-tests.json').write_text(json.dumps(report,indent=2));print(report)
