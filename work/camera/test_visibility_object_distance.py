from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_distance;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
rng=random.Random(0x20a0)
for case in range(1024):
 matrix=rng.randbytes(48);obj=rng.randbytes(164);u.mem_write(0x02000054,struct.pack('<I',0x02000100));u.mem_write(0x02000100,matrix);u.mem_write(0x02000200,obj)
 u.reg_write(UC_ARM_REG_R7,0x02000000);u.reg_write(UC_ARM_REG_R6,0x02000200);u.emu_start(0x0300209c,0x030020f0,count=100)
 m=C.create_string_buffer(matrix);o=C.create_string_buffer(obj);out=(C.c_uint32*3)()
 assert fn(m,o,out)==1 and list(out)==[u.reg_read(UC_ARM_REG_R2),u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R4)]
 assert struct.unpack('<I',u.mem_read(0x02000228,4))[0]==out[2] and o.raw[:164]==obj
report=dict(result='PASS',original_ARM_synthetic_cases=1024,scope='Object camera X/Z and wrapped distance only, not list sorting or rendering.')
(root/'visibility-object-distance-tests.json').write_text(json.dumps(report,indent=2));print(report)
