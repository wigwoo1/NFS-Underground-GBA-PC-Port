"""Original insertion leaf beyond native20-record transport; isolated emulator only."""
from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in ((0x02000000,0x40000),(0x03000000,0x10000)):u.mem_map(address,size)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
f=C.CDLL(str((p/'visibility-probe.dll').resolve())).nfs_visibility_insert;f.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
results=[]
for index in (19,20,21,31):
 groups=bytearray(4096);descriptor=86
 u.mem_write(0x02001000,bytes(groups));u.mem_write(0x02000060,struct.pack('<2I',0x02003000,0x02001000))
 u.mem_write(0x03007e0c,struct.pack('<I',descriptor));u.mem_write(0x03007e60,struct.pack('<I',index))
 for reg,value in ((UC_ARM_REG_R9,0x02000000),(UC_ARM_REG_R7,0x02003000+index*16),(UC_ARM_REG_SP,0x03007e00)):u.reg_write(reg,value)
 u.emu_start(0x03002f14,0x03002f60,count=1000);assert u.reg_read(UC_ARM_REG_PC)==0x03002f60
 group=bytes(u.mem_read(0x02001000+descriptor*8,8));next_index=(u.reg_read(UC_ARM_REG_R7)-0x02003000)//16;total=struct.unpack('<I',u.mem_read(0x03007e60,4))[0]
 assert group[:2]==bytes((1,index)) and next_index==index+1 and total==index+1
 g=C.create_string_buffer(bytes(groups));n=C.c_uint32(index);t=C.c_uint32(index);ok=f(g,512,descriptor,20,C.byref(n),C.byref(t))
 assert bool(ok)==(index<20)
 if not ok:assert g.raw[:4096]==groups and n.value==t.value==index
 results.append(dict(index=index,original_next=next_index,original_total=total,native_accepted=bool(ok)))
report=dict(result='PASS',cases=results,scope='Original insertion leaf has no20-entry clamp in these cases. Does not establish allocated queue capacity or whole-builder overflow behavior. Native bounds unchanged.')
(p/'visibility-overflow-leaf-tests.json').write_text(json.dumps(report,indent=2));print(report)
