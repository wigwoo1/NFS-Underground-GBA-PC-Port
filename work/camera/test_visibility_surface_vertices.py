from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x03000000,0x10000),(0x02000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);u.mem_write(0x08000000,rom)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_surface_vertices
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700]);rng=random.Random(0x1d34)
for case in range(1024):
 scratch=bytearray(rng.randbytes(52));struct.pack_into('<2h',scratch,4,rng.randrange(1,32768),rng.randrange(1,32768));flags=8 if case&1 else 0;struct.pack_into('<H',scratch,0x30,flags)
 heights=[rng.getrandbits(32) for _ in range(4)];attrs=[rng.getrandbits(32) for _ in range(4)];params=[rng.getrandbits(32),120,80,rng.choice([0,1,8,31,32,256,257]),rng.getrandbits(16),case&2]
 initial=rng.randbytes(48);u.mem_write(0x02000000,bytes(scratch));u.mem_write(0x02000200,initial);sp=0x02001000
 for off,val in [(0x4c,params[0]),(0x54,120),(0x50,80),(0x40,1),(0x18,params[5]),(0x20,params[3]),(0x1c,params[4]),(0x34,0),(0xc,heights[2]),(8,heights[3]),(0x30,attrs[0]),(0x28,attrs[1]),(0x2c,attrs[2]),(0x24,attrs[3])]:u.mem_write(sp+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R5,0x02000000),(UC_ARM_REG_R6,flags),(UC_ARM_REG_R8,0x02000200),(UC_ARM_REG_R9,heights[0]),(UC_ARM_REG_R10,heights[1]),(UC_ARM_REG_SP,sp)]:u.reg_write(reg,val)
 u.emu_start(0x03001cb4,0x03001ec8,count=500);assert u.reg_read(UC_ARM_REG_PC)==0x03001ec8
 out=C.create_string_buffer(initial);count=C.c_uint(99);s=C.create_string_buffer(bytes(scratch));h=(C.c_uint32*4)(*heights);a=(C.c_uint32*4)(*attrs);p=(C.c_uint32*6)(*params)
 assert fn(s,h,a,p,recip,out,48,C.byref(count))==1
 assert count.value==struct.unpack('<I',u.mem_read(sp+0x34,4))[0]
 assert out.raw[:48]==bytes(u.mem_read(0x02000200,48)),case
 out=C.create_string_buffer(initial);count=C.c_uint(99)
 assert fn(s,h,a,p,recip,out,(48 if flags else 24)-1,C.byref(count))==0 and out.raw[:48]==initial and count.value==99
report=dict(result='PASS',original_ARM_synthetic_cases=1024,atomic_capacity_failures=1024,scope='Surface projected vertex stream, affine/perspective and clipped-start emission; not complete region composition or live rendering.')
(root/'visibility-surface-vertices-tests.json').write_text(json.dumps(report,indent=2));print(report)
