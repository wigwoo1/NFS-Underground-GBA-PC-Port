from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
for address,size in [(0x03000000,0x10000),(0x02000000,0x40000),(0x08000000,0x800000)]:u.mem_map(address,size)
u.mem_write(0x08000000,rom)
d=C.CDLL(str((root/'native_rotation.dll').resolve()));d.nfs_rotation_combine.argtypes=[C.c_void_p]*3
def native(a,b):
    ab=C.create_string_buffer(a);bb=C.create_string_buffer(b);out=C.create_string_buffer(48)
    d.nfs_rotation_combine(ab,bb,out);return out.raw
r=random.Random(0x6db14)
for case in range(1000):
    a=r.randbytes(48) if case%2 else struct.pack('<12i',*[r.randint(-16384,16384) for _ in range(12)])
    b=r.randbytes(48) if case%2 else struct.pack('<12i',*[r.randint(-16384,16384) for _ in range(12)])
    for alias,address in [('none',0x02002000),('left',0x02000000),('right',0x02001000)]:
        u.mem_write(0x02000000,a);u.mem_write(0x02001000,b)
        for reg,value in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02001000),(UC_ARM_REG_R2,address),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03007001)]:u.reg_write(reg,value)
        u.emu_start(0x0806db15,0x03007000,count=1000)
        ab=C.create_string_buffer(a);bb=C.create_string_buffer(b);out=C.create_string_buffer(48)
        dest=ab if alias=='left' else bb if alias=='right' else out
        d.nfs_rotation_combine(ab,bb,dest)
        assert dest.raw[:48]==bytes(u.mem_read(address,48)),(case,alias)
report={'result':'PASS','differential_cases':3000,'buffer_modes':['disjoint','output equals left','output equals right'],
        'scope':'Exact integer rotation combination including wrapping and translation addition; not smooth presentation.'}
(root/'native-rotation-tests.json').write_text(json.dumps(report,indent=2));print(report)
