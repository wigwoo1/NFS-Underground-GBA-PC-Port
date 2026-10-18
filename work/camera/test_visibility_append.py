from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_append
fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_uint]
r=random.Random(0x556c);appended=0
for case in range(600):
    queue=r.randbytes(320);source=bytearray(r.randbytes(16));struct.pack_into('<H',source,0,7)
    target=65535 if case%5==0 else r.randrange(512);left=r.randrange(65536);right=r.randrange(65536)
    next_index=r.randrange(20);total=r.getrandbits(32);linked=0xffffffff if case%2 else r.getrandbits(32)
    u.mem_write(0x02008000,queue);u.mem_write(0x02007300,bytes(source))
    for a,v in [(0x02000014,0x02001000),(0x02000050,0x02007000),(0x02007004,0x02007100),
                (0x02007200,0x02008000+next_index*16),(0x02007204,total),(0x02007208,linked),
                (0x03007e00,0x02007204)]:u.mem_write(a,struct.pack('<I',v))
    u.mem_write(0x02001000+7*48+32,struct.pack('<H',target))
    u.mem_write(0x02007100,struct.pack('<I',left));u.mem_write(0x02007108,struct.pack('<I',right))
    for reg,v in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02007200),(UC_ARM_REG_R2,0x02007300),(UC_ARM_REG_R3,0x02007208),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,v)
    u.emu_start(0x0300556c,0x03006000,count=1000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
    q=C.create_string_buffer(queue);n=C.c_uint32(next_index);t=C.c_uint32(total);l=C.c_uint32(linked)
    assert fn(q,20,C.byref(n),C.byref(t),C.byref(l),C.create_string_buffer(bytes(source)),target,left,right)
    assert q.raw[:320]==bytes(u.mem_read(0x02008000,320))
    assert (0x02008000+n.value*16,t.value,l.value)==struct.unpack('<3I',u.mem_read(0x02007200,12))
    appended+=target!=65535
# Full queues reject a real link atomically; absent links remain a no-op.
original=q.raw;n.value=20;sentinel=(n.value,t.value,l.value)
assert not fn(q,20,C.byref(n),C.byref(t),C.byref(l),C.create_string_buffer(bytes(source)),2,0,238)
assert q.raw==original and (n.value,t.value,l.value)==sentinel
assert fn(q,20,C.byref(n),C.byref(t),C.byref(l),C.create_string_buffer(bytes(source)),65535,0,238)
assert q.raw==original and (n.value,t.value,l.value)==sentinel
report=dict(result='PASS',original_ARM_cases=600,appended=appended,absent_links=600-appended,
            full_queue_atomic=True,scope='Linked descriptor queue append only; no complete native visibility traversal.')
(root/'visibility-append-tests.json').write_text(json.dumps(report,indent=2));print(report)
