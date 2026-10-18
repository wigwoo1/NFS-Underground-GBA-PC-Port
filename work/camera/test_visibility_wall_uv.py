from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_wall_uv
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
rng=random.Random(1800);cases=0
for exponent in [0,1,2,16,31,32,33,34,255,256,257,258,65535]:
 for flip in [0,2]:
  for trial in range(40):
   source=bytearray(rng.randbytes(68));material=bytearray(rng.randbytes(32));initial=rng.randbytes(52)
   flags=(rng.getrandbits(16)&~2)|flip;struct.pack_into('<H',source,0x2e,flags);struct.pack_into('<H',material,0x1a,exponent)
   ub,vo,extent=[rng.getrandbits(32) for _ in range(3)]
   u.mem_write(0x02000000,bytes(source));u.mem_write(0x02000100,bytes(material));u.mem_write(0x02000200,initial)
   u.mem_write(0x02001010,struct.pack('<2I',0x02000100,extent))
   for reg,val in [(UC_ARM_REG_R7,0x02000000),(UC_ARM_REG_R5,0x02000200),(UC_ARM_REG_R0,vo),(UC_ARM_REG_LR,ub),(UC_ARM_REG_SP,0x02001000)]:u.reg_write(reg,val)
   u.emu_start(0x03001a7c,0x03001b0c,count=100)
   assert u.reg_read(UC_ARM_REG_PC)==0x03001b0c
   out=C.create_string_buffer(initial);src=C.create_string_buffer(bytes(source));mat=C.create_string_buffer(bytes(material))
   assert fn(src,mat,ub,vo,extent,out)==1
   assert out.raw[:52]==bytes(u.mem_read(0x02000200,52)),(exponent,flip,trial)
   assert src.raw[:68]==source and mat.raw[:32]==material
   cases+=1
out=C.create_string_buffer(initial)
assert fn(None,mat,ub,vo,extent,out)==0 and out.raw[:52]==initial
assert fn(src,None,ub,vo,extent,out)==0 and out.raw[:52]==initial
assert fn(src,mat,ub,vo,extent,None)==0
report=dict(result='PASS',original_ARM_synthetic_cases=cases,exponents_tested=13,invalid_pointer_checks=3,scope='Wall UV scratch arithmetic only; synthetic boundary fixtures, no captured full-wall rendering or clipping.')
(root/'visibility-wall-uv-tests.json').write_text(json.dumps(report,indent=2));print(report)
