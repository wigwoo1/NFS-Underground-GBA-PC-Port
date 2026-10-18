from pathlib import Path
import ctypes as C,random,struct,sys,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x08000000,0x800000)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
d=C.CDLL(str((root/'native_wall.dll').resolve()));fn=d.nfs_wall_texture_step
fn.argtypes=[C.c_uint32,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);r=random.Random(0x52d0);out=C.c_uint32()
for case in range(4000):
 span=r.getrandbits(32);rows=[0,1,2,32767][case%4] if case<40 else r.randrange(32768);extended=case%2
 for reg,value in [(UC_ARM_REG_R0,span),(UC_ARM_REG_R1,rows),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 u.emu_start(0x0300527c if extended else 0x030052d0,0x03007000,count=100)
 assert fn(span,rows,table,extended,C.byref(out)) and out.value==u.reg_read(UC_ARM_REG_R0)
# For interior, un-clipped columns the observed dispatch count includes the
# extra terminal row, while the texture division uses one fewer row.
active=None;checked=0;mismatch=[]
for e in records(root/'shading-spans.bin'):
 if e['pc']==0x03000304:active=e
 if e['pc']!=0x030053e8 or active is None or active['regs'][2]&128:continue
 state=e['blocks'][75][1];top=struct.unpack_from('<I',state,4)[0]>>14;n=e['regs'][3]
 if top<=1 or top+n>=158 or n<2:continue
 span=struct.unpack_from('<I',active['blocks'][6][1],28)[0]
 assert fn(span,n-1,table,0,C.byref(out))
 actual=struct.unpack_from('<I',state,44)[0]
 if out.value!=actual:mismatch.append(e['id'])
 checked+=1
assert checked and not mismatch,(checked,mismatch[:10])
assert not fn(0,32768,table,0,C.byref(out))
report=dict(result='PASS',original_ARM_cases=4000,interior_live_columns=checked,
 scope='Default and extended texture-step helper equivalence; live default spans use dispatch count minus the original extra terminal row. Continuous 4K UV mapping remains distinct.')
(root/'wall-texture-step-tests.json').write_text(json.dumps(report,indent=2));print(report)
