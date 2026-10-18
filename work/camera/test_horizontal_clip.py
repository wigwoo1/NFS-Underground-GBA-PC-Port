from pathlib import Path
import ctypes as C, json, random, struct, sys
sys.path.insert(0, str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
root = Path('work/camera')
rom = Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
u.mem_map(0x02000000, 0x40000); u.mem_map(0x03000000, 0x10000)
u.mem_write(0x03000000, rom[0x71b0c:0x77b0c])
def stop(cpu, address, size, context):
    cpu.emu_stop()
u.hook_add(UC_HOOK_CODE, stop, begin=0x0300066c, end=0x0300066c)
fn = C.CDLL(str((root/'native_wall.dll').resolve())).nfs_wall_clip_horizontal
fn.argtypes = [C.c_int, C.c_int, C.c_uint, C.c_uint, C.POINTER(C.c_int)]
r = random.Random(0x5a0)
cases = [(92,135,92,98), (-3,3,0,238), (0,4,0,2), (0,3,0,238)]
cases += [(r.randrange(-32768,32768), r.randrange(-32768,32768),
           r.randrange(65536), r.randrange(65536)) for _ in range(2000)]
cases += [(r.randrange(-40,240), r.randrange(0,280),
           r.randrange(0,120), r.randrange(120,240)) for _ in range(2000)]
visible = early_rejected = 0
for lp,rp,lo,hi in cases:
    left,right=lp>>1,(rp+1)>>1
    out=(C.c_int*4)()
    assert fn(lp,rp,lo,hi,out)
    if right-left<=1:
        assert list(out)==[0,0,0,0]; early_rejected+=1; continue
    sp=0x03007d00
    u.mem_write(sp,bytes(0x100))
    u.mem_write(0x020000e2,struct.pack('<2H',lo,hi))
    for offset,value in [(0x44,0x02000000),(0x40,left),(0x3c,right)]:
        u.mem_write(sp+offset,struct.pack('<I',value&0xffffffff))
    u.reg_write(UC_ARM_REG_SP,sp); u.reg_write(UC_ARM_REG_R6,right-left)
    u.emu_start(0x030005a0,0x03000674,count=1000)
    accepted=u.reg_read(UC_ARM_REG_PC)==0x03000674
    assert out[0]==accepted,(lp,rp,lo,hi,list(out))
    if accepted:
        actual_left=struct.unpack('<i',u.mem_read(sp+0x40,4))[0]
        assert list(out)==[1,actual_left,u.reg_read(UC_ARM_REG_R6),actual_left-left]
        visible+=1
sentinel=(C.c_int*4)(9,8,7,6)
assert not fn(-32769,0,0,238,sentinel) and list(sentinel)==[9,8,7,6]
report=dict(result='PASS',cases=len(cases),original_ARM_block_cases=len(cases)-early_rejected,
            early_narrow_rejection_cases=early_rejected,visible=visible,invalid_input_preserves_output=True,
            scope='Native horizontal clipping versus original ARM block; initial narrow rejection checked separately. No world-space visibility producer or live motion integration.')
(root/'horizontal-clip-tests.json').write_text(json.dumps(report,indent=2));print(report)
