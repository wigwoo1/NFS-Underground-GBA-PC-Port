from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_material;fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p];rng=random.Random(23);lod=0;forced=0
for case in range(2048):
 obj=bytearray(rng.randbytes(164));flags=case%256;struct.pack_into('<H',obj,10,flags);struct.pack_into('<h',obj,0x36,[-1,0,1,32767][case%4]);depth=[0,1023,1024,1025,8191,0xffffffff][case%6];base=rng.getrandbits(32)
 u.mem_write(0x02000300,bytes(obj));u.mem_write(0x02000024,struct.pack('<I',base))
 for reg,val in [(UC_ARM_REG_R6,0x02000000),(UC_ARM_REG_R7,0x02000300),(UC_ARM_REG_IP,depth),(UC_ARM_REG_LR,flags)]:u.reg_write(reg,val)
 u.emu_start(0x030023b8,0x03002410,count=100)
 b=C.create_string_buffer(bytes(obj));out=(C.c_uint32*2)();assert fn(b,base,depth,out)==1
 assert b.raw[:164]==bytes(u.mem_read(0x02000300,164)) and list(out)==[u.reg_read(UC_ARM_REG_R4),u.reg_read(UC_ARM_REG_IP)]
 forced+=out[1]==512 and depth!=512
report=dict(result='PASS',original_ARM_material_cases=2048,forced_depth512_cases=forced,scope='Material/animation offset and effective depth selection only; no material reads or draw dispatch.')
(root/'visibility-object-material-tests.json').write_text(json.dumps(report,indent=2));print(report)
