from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
f=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_billboard_material;f.argtypes=[C.c_void_p]*4;rng=random.Random(0x24d8);selected=0;rejected=0
for case in range(1024):
 m=bytearray(rng.randbytes(64))
 if case%3==0:struct.pack_into('<HH',m,0x16,0,0)
 elif case%3==1:struct.pack_into('<H',m,0x16,0)
 p=(C.c_uint32*4)(rng.choice([0,4095,4096,8191,0xffffffff]),rng.randrange(2),rng.getrandbits(32),rng.getrandbits(32))
 u.mem_write(0x02000400,bytes(m));u.mem_write(0x02000804,struct.pack('<I',p[2]));u.mem_write(0x02018004,struct.pack('<II',p[3],p[0]))
 for reg,val in [(UC_ARM_REG_R4,0x02000400),(UC_ARM_REG_R6,0x02000800),(UC_ARM_REG_R9,p[1]),(UC_ARM_REG_R10,struct.unpack_from('<H',m,8)[0]),(UC_ARM_REG_R8,struct.unpack_from('<H',m,10)[0]),(UC_ARM_REG_SP,0x02018000)]:u.reg_write(reg,val)
 cpsr=u.reg_read(UC_ARM_REG_CPSR)&~(1<<30)
 if struct.unpack_from('<H',m,0x16)[0]==0:cpsr|=1<<30
 u.reg_write(UC_ARM_REG_CPSR,cpsr);u.emu_start(0x030024d8,0x0300252c,count=100)
 off=u.reg_read(UC_ARM_REG_R4)-0x02000400
 expected=[u.reg_read(UC_ARM_REG_R10),u.reg_read(UC_ARM_REG_R8),struct.unpack('<I',u.mem_read(0x02018004,4))[0],struct.unpack_from('<H',m,off+0x1a)[0],struct.unpack_from('<H',m,off+10)[0],off]
 out=(C.c_uint32*6)();a=C.create_string_buffer(bytes(m[:32]));b=C.create_string_buffer(bytes(m[32:]));assert f(a,b,p,out) and list(out)==expected,(case,list(out),expected)
 if off:
  selected+=1;before=bytes(out);assert not f(a,None,p,out) and bytes(out)==before;rejected+=1
report=dict(result='PASS',original_ARM_selection_cases=1024,distant_material_cases=selected,missing_material_atomic=rejected,scope='Synthetic alternate-path material/UV selection; no clipping, rasterization or live path coverage.')
(root/'visibility-object-billboard-material-tests.json').write_text(json.dumps(report,indent=2));print(report)

