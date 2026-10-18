from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_texture;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p]
def hook(uc,pc,size,ctx):
 if pc in (0x03002460,0x03002588):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook);rng=random.Random(2410);branches=[0,0];missing=0
for case in range(2048):
 obj=bytearray(rng.randbytes(164));flags=8 if case%2 else 0;struct.pack_into('<H',obj,10,flags);signed=[-1,0,1,32767][(case//2)%4];struct.pack_into('<h',obj,0x36,signed);depth=[0,1024,1025,8191,0xffffffff][case%5];base=rng.getrandbits(32);material=rng.randbytes(32);previous=rng.randbytes(32)
 u.mem_write(0x02000300,bytes(obj));u.mem_write(0x02000004,struct.pack('<I',base));u.mem_write(0x02000400,previous+material)
 u.reg_write(UC_ARM_REG_CPSR,0x10|(0 if flags else 0x40000000))
 for reg,val in [(UC_ARM_REG_R6,0x02000000),(UC_ARM_REG_R7,0x02000300),(UC_ARM_REG_R4,0x02000420),(UC_ARM_REG_IP,depth),(UC_ARM_REG_R9,signed&0xffffffff),(UC_ARM_REG_SP,0x02008000)]:u.reg_write(reg,val)
 u.emu_start(0x03002410,0x03002590,count=100)
 out=(C.c_uint32*2)();assert fn(C.create_string_buffer(bytes(obj)),C.create_string_buffer(material),C.create_string_buffer(previous),base,depth,out)==1
 branch=int(u.reg_read(UC_ARM_REG_PC)==0x03002460)
 assert list(out)==[struct.unpack('<I',u.mem_read(0x02008004,4))[0],branch],case
 branches[branch]+=1
 if flags and depth in (1025,8191):
  before=bytes(out);assert not fn(C.create_string_buffer(bytes(obj)),C.create_string_buffer(material),None,base,depth,out) and bytes(out)==before;missing+=1
report=dict(result='PASS',original_ARM_texture_cases=2048,branch_counts=branches,missing_previous_atomic=missing,scope='Texture pointer and branch only; neither draw path implemented by this helper.')
(root/'visibility-object-texture-tests.json').write_text(json.dumps(report,indent=2));print(report)
