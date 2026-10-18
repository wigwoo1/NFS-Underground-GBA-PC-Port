from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
def stop(cpu,address,length,context):cpu.emu_stop()
u.hook_add(UC_HOOK_CODE,stop,begin=0x03002f60,end=0x03002f60)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_edge_record
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
r=random.Random(0x2e18);accepted=0
for case in range(1200):
    source=r.randbytes(16);initial=r.randbytes(16)
    p=[r.randrange(-200,500),r.randrange(-200,500),r.choice([2047,2048,2049,4096]),r.randrange(-100,6000),
       r.choice([0,8,16,24]),r.getrandbits(16),r.randrange(512),0,238,r.randrange(160),r.randrange(160)]
    u.mem_write(0x02001000,source);u.mem_write(0x02002000,initial)
    u.mem_write(0x020000e2,struct.pack('<2H',p[7],p[8]));u.mem_write(0x0200005c,struct.pack('<2H',p[9],p[10]))
    u.mem_write(0x0200302e,struct.pack('<H',p[5]))
    for off,v in [(4,p[4]),(0x38,0x02001000),(0x10,0x02003000),(0xc,p[6])]:u.mem_write(0x03007e00+off,struct.pack('<I',v))
    for reg,v in [(UC_ARM_REG_R5,p[0]),(UC_ARM_REG_R6,p[1]),(UC_ARM_REG_R10,p[2]),(UC_ARM_REG_R8,p[3]),(UC_ARM_REG_R9,0x02000000),(UC_ARM_REG_R7,0x02002000),(UC_ARM_REG_SP,0x03007e00)]:u.reg_write(reg,v&0xffffffff)
    u.emu_start(0x03002e18,0x03002f14,count=1000)
    original_accept=u.reg_read(UC_ARM_REG_PC)==0x03002f14
    out=C.create_string_buffer(initial);result=fn(C.create_string_buffer(source),(C.c_int32*11)(*p),out)
    assert result==original_accept and out.raw[:16]==bytes(u.mem_read(0x02002000,16)),case
    accepted+=result
out=C.create_string_buffer(initial);p[6]=65536
assert fn(C.create_string_buffer(source),(C.c_int32*11)(*p),out)==-1 and out.raw[:16]==initial
report=dict(result='PASS',original_ARM_cases=1200,accepted=accepted,culled=1200-accepted,invalid_preserves_output=True,
            scope='Projected-edge candidate gate and visibility record construction. Camera transform, near clipping, projection and membership insertion remain separate.')
(root/'visibility-edge-tests.json').write_text(json.dumps(report,indent=2));print(report)
