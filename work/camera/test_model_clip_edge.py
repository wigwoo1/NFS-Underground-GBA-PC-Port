import sys,ctypes as C,struct,random
from pathlib import Path
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x71b0c+0x6000]);lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nfs_model_clip_edge;fn.argtypes=[C.c_int32,C.c_int32,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer(rom[0x627700:0x647700]);rng=random.Random(0x3fcc)
for case in range(1000):
 axis=case%2;uv=case%3!=0;p=[rng.randrange(-100,341),rng.randrange(-100,341),rng.randrange(65536),rng.randrange(65536),rng.randrange(-100,341),rng.randrange(-100,341),rng.randrange(65536),rng.randrange(65536)]
 data=struct.pack('<8i',*p)+bytes(32)+struct.pack('<I',uv);u.mem_write(0x02001000,data)
 for reg,v in [(UC_ARM_REG_R0,0),(UC_ARM_REG_R1,240),(UC_ARM_REG_R2,0x02001000),(UC_ARM_REG_R3,axis),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,v)
 u.emu_start(0x03003fcc,0x03007000,count=2000);expected=u.reg_read(UC_ARM_REG_R0);out=(C.c_int32*8)(*p);flags=C.c_uint();assert fn(0,240,axis,uv,(C.c_int32*8)(*p),table,out,C.byref(flags))
 assert flags.value==expected,(case,flags.value,expected)
 if expected:assert bytes(out)==bytes(u.mem_read(0x02001000,32)),(case,list(out),struct.unpack('<8i',bytes(u.mem_read(0x02001000,32))))
 else:assert list(out)==p
print('PASS1000 original ARM clipped edge XY/UV/flags comparisons, both axes and optional UV')
