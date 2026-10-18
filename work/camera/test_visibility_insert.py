from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_insert
fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
r=random.Random(0x2f14)
for case in range(700):
    groups=bytearray(r.randbytes(4096));descriptor=r.randrange(512);groups[descriptor*8]=case%7
    index=r.randrange(20);total=0xffffffff if case%2 else r.getrandbits(32)
    u.mem_write(0x02001000,bytes(groups));u.mem_write(0x02000060,struct.pack('<2I',0x02003000,0x02001000))
    u.mem_write(0x03007e0c,struct.pack('<I',descriptor));u.mem_write(0x03007e60,struct.pack('<I',total))
    for reg,value in [(UC_ARM_REG_R9,0x02000000),(UC_ARM_REG_R7,0x02003000+index*16),(UC_ARM_REG_SP,0x03007e00)]:u.reg_write(reg,value)
    u.emu_start(0x03002f14,0x03002f60,count=1000);assert u.reg_read(UC_ARM_REG_PC)==0x03002f60
    g=C.create_string_buffer(bytes(groups));n=C.c_uint32(index);t=C.c_uint32(total)
    assert fn(g,512,descriptor,20,C.byref(n),C.byref(t))
    assert g.raw[:4096]==bytes(u.mem_read(0x02001000,4096))
    assert 0x02003000+n.value*16==u.reg_read(UC_ARM_REG_R7)
    assert t.value==struct.unpack('<I',u.mem_read(0x03007e60,4))[0]
# Reject unrepresentable eighth members and full queues without publishing changes.
for members,index,descriptor in [(7,0,0),(255,0,0),(0,20,0),(0,0,512)]:
    groups=bytearray(4096);groups[0]=members;g=C.create_string_buffer(bytes(groups));n=C.c_uint32(index);t=C.c_uint32(17)
    assert not fn(g,512,descriptor,20,C.byref(n),C.byref(t))
    assert g.raw[:4096]==groups and (n.value,t.value)==(index,17)
report=dict(result='PASS',original_ARM_valid_cases=700,atomic_rejection_cases=4,
            scope='Membership insertion within queue/group capacity. Original overflowing membership behavior is deliberately rejected, not emulated.')
(root/'visibility-insert-tests.json').write_text(json.dumps(report,indent=2));print(report)
