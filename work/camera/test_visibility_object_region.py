from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_region;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
rng=random.Random(0x2320)
for case in range(512):
 state=bytearray(rng.randbytes(256));obj=bytearray(rng.randbytes(164));flags=struct.unpack_from('<H',obj,10)[0]|16;struct.pack_into('<H',obj,10,flags);struct.pack_into('<H',obj,0x36,case)
 initial=rng.randbytes(16);sp=0x03007000;u.mem_write(0x02000000,bytes(obj));u.mem_write(sp+0x48,initial)
 bounds=struct.unpack_from('<4H',state,0xe2)
 for reg,val in [(UC_ARM_REG_R7,0x02000000),(UC_ARM_REG_R6,0x02000100),(UC_ARM_REG_R0,bounds[0]),(UC_ARM_REG_R1,bounds[1]),(UC_ARM_REG_R8,bounds[2]),(UC_ARM_REG_R10,bounds[3]),(UC_ARM_REG_LR,flags),(UC_ARM_REG_SP,sp)]:u.reg_write(reg,val)
 u.emu_start(0x03002320,0x03002360,count=100)
 out=C.create_string_buffer(initial);st=C.create_string_buffer(bytes(state));ob=C.create_string_buffer(bytes(obj))
 assert fn(st,ob,out)==1 and out.raw[:16]==bytes(u.mem_read(sp+0x48,16))
 assert u.reg_read(UC_ARM_REG_R2)==0 and u.reg_read(UC_ARM_REG_R1)==sp+0x48
 struct.pack_into('<H',obj,10,flags&~16);out=C.create_string_buffer(initial)
 assert fn(st,C.create_string_buffer(bytes(obj)),out)==0 and out.raw[:16]==initial
obj=bytearray(164);struct.pack_into('<H',obj,10,16);struct.pack_into('<H',obj,0x36,512);out=C.create_string_buffer(initial)
assert fn(st,C.create_string_buffer(bytes(obj)),out)==-1 and out.raw[:16]==initial
report=dict(result='PASS',original_ARM_object_region_cases=512,non_region_objects_unchanged=512,invalid_region_atomic=True,scope='Object flag10 region-record construction only, not object traversal/projection/rendering.')
(root/'visibility-object-region-tests.json').write_text(json.dumps(report,indent=2));print(report)
