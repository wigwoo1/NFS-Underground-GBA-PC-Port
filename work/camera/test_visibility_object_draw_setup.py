from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_draw_setup;fn.argtypes=[C.c_void_p]*5;rng=random.Random(2284)
for case in range(1024):
 state=rng.randbytes(256);record=rng.randbytes(16);obj=rng.randbytes(164);matrix=rng.randbytes(48)
 for address,data in [(0x02000000,state),(0x02000200,record),(0x02000300,obj),(0x02000400,matrix),(0x02008014,struct.pack('<I',0x02000400)),(0x02008024,struct.pack('<I',0x02000200))]:u.mem_write(address,data)
 for reg,value in [(UC_ARM_REG_SP,0x02008000),(UC_ARM_REG_R6,0x02000000),(UC_ARM_REG_R7,0x02000300)]:u.reg_write(reg,value)
 u.emu_start(0x03002284,0x03002320,count=100)
 b=C.create_string_buffer(state);xyz=(C.c_uint32*3)();assert fn(b,C.create_string_buffer(record),C.create_string_buffer(obj),C.create_string_buffer(matrix),xyz)==1
 expected=[struct.unpack('<I',u.mem_read(0x02008000+off,4))[0] for off in (16,12,8)]
 assert list(xyz)==expected and b.raw[:256]==bytes(u.mem_read(0x02000000,256))
report=dict(result='PASS',original_ARM_draw_setup_cases=1024,scope='XYZ and horizontal bounds setup only; render dispatch/projection not ported.')
(root/'visibility-object-draw-setup-tests.json').write_text(json.dumps(report,indent=2));print(report)
