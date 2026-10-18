from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_transform
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
r=random.Random(0x2c80)
for case in range(900):
    points=[r.getrandbits(32) for _ in range(6)];matrix=[r.getrandbits(32) for _ in range(12)]
    if case%2:
        points=[r.randrange(-30000,30000)&0xffffffff for _ in range(6)]
        matrix=[r.randrange(-16384,16385)&0xffffffff for _ in range(12)]
    index=case%3;next_index=(index+1)%3
    for i in range(3):u.mem_write(0x02001000+i*68,struct.pack('<2I',*points[i*2:i*2+2]))
    for offset,value in [(0,index+1),(0x14,3),(0x18,0x02001000),(0x10,0x02001000+index*68),
                         (0x30,matrix[0]),(0x2c,matrix[6]),(0x28,matrix[9]),(0x24,matrix[2]),(0x20,matrix[8]),(0x1c,matrix[11])]:
        u.mem_write(0x03007e00+offset,struct.pack('<I',value))
    u.mem_write(0x02000050,struct.pack('<I',0x02002000))
    for reg,value in [(UC_ARM_REG_R3,0x02001000+index*68),(UC_ARM_REG_R0,index*68),(UC_ARM_REG_R9,0x02000000),(UC_ARM_REG_SP,0x03007e00)]:u.reg_write(reg,value)
    u.emu_start(0x03002c80,0x03002d20,count=1000);assert u.reg_read(UC_ARM_REG_PC)==0x03002d20
    selected=points[index*2:index*2+2]+points[next_index*2:next_index*2+2]
    out=(C.c_uint32*4)();assert fn((C.c_uint32*4)(*selected),(C.c_uint32*12)(*matrix),out)
    assert list(out)==[u.reg_read(reg) for reg in [UC_ARM_REG_R5,UC_ARM_REG_R10,UC_ARM_REG_R6,UC_ARM_REG_R8]],case
report=dict(result='PASS',original_ARM_cases=900,closing_ring_edges=300,
            scope='Native planar world-to-camera edge transform with original integer wrapping. Continuous camera-pose visibility and full builder orchestration remain separate.')
(root/'visibility-transform-tests.json').write_text(json.dumps(report,indent=2));print(report)
