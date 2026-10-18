from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import *
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);rng=random.Random(0x5058)
f=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_billboard_raster;f.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32]
for case in range(512):
 texture=bytes(rng.randrange(0,8) for _ in range(16384));initial=rng.randbytes(240*160);c=(C.c_uint32*8)(rng.randrange(0,100),rng.randrange(0,80),rng.randrange(1,60),rng.randrange(1,40),rng.randrange(16)<<16,rng.randrange(16)<<16,rng.randrange(1,65536),rng.randrange(1,65536));shift=7
 u.mem_write(0x02010000,texture);u.mem_write(0x02020000,initial);proj=bytearray(16);struct.pack_into('<I',proj,0,0x02020000);struct.pack_into('<I',proj,12,240);u.mem_write(0x02000400,bytes(proj));ctx=bytearray(44);struct.pack_into('<H',ctx,36,shift);struct.pack_into('<I',ctx,40,0x02010000);u.mem_write(0x02000600,bytes(ctx))
 for off,val in [(0x1c,0x02000400),(0x20,0x02000600),(8,c[7]),(12,c[4])]:u.mem_write(0x02008000+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_SP,0x02008000),(UC_ARM_REG_R6,c[0]),(UC_ARM_REG_LR,c[1]),(UC_ARM_REG_R4,c[2]),(UC_ARM_REG_R7,c[3]),(UC_ARM_REG_R5,c[5]),(UC_ARM_REG_R8,c[6])]:u.reg_write(reg,val)
 u.emu_start(0x03005058,0x030050ec,count=100000)
 out=C.create_string_buffer(initial);tex=C.create_string_buffer(texture);assert f(c,shift,tex,len(texture),out,len(initial),240)==1
 assert out.raw[:len(initial)]==bytes(u.mem_read(0x02020000,len(initial))),case
 # Reject a framebuffer ending before the final destination, preserving every byte.
 badsize=(c[1]+c[3]-1)*240+(c[0]&~1)+2*(c[2]-1)
 untouched=C.create_string_buffer(initial);assert f(c,shift,tex,len(texture),untouched,badsize,240)==0 and untouched.raw[:len(initial)]==initial
report=dict(result='PASS',original_ARM_pixel_loop_cases=512,late_framebuffer_rejections=512,scope='Original-resolution byte-lane diagnostic raster; not 4K rendering or live integration.')
(root/'visibility-billboard-raster-tests.json').write_text(json.dumps(report,indent=2));print(report)
