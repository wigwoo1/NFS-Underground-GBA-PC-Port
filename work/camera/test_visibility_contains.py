from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_contains
fn.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p]
r=random.Random(0x4bf4);accepted=0;rejected=0;cases=[]
# Correct orientation, boundary, exterior, reverse orientation and empty ring.
square=[(0,0),(0,100),(100,100),(100,0)]
for ring in [square,list(reversed(square)),[],[(0,0)]]:
    for point in [(50,50),(0,0),(0,50),(100,50),(101,50),(-1,50)]:cases.append((ring,point))
for case in range(1000):
    n=r.randrange(33)
    draw=(lambda:r.getrandbits(32)) if case%2 else (lambda:r.randrange(-30000,30001)&0xffffffff)
    cases.append(([(draw(),draw()) for _ in range(n)],(draw(),draw())))
for case,(ring,(x,z)) in enumerate(cases):
    data=b''.join(struct.pack('<2I',a&0xffffffff,b&0xffffffff)+bytes(60) for a,b in ring)
    descriptor=case%512
    if data:u.mem_write(0x02001000,data)
    u.mem_write(0x03007e00,struct.pack('<2I',len(ring),descriptor))
    for reg,value in [(UC_ARM_REG_R1,x&0xffffffff),(UC_ARM_REG_R2,z&0xffffffff),(UC_ARM_REG_R3,0x02001000),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,value)
    u.emu_start(0x03004bf4,0x03006000,count=2000)
    assert u.reg_read(UC_ARM_REG_PC)==0x03006000
    out=C.c_uint32(0xcccccccc);buf=C.create_string_buffer(data)
    assert fn(buf,len(data),len(ring),x,z,descriptor,C.byref(out))
    assert out.value==u.reg_read(UC_ARM_REG_R0),(case,out.value,u.reg_read(UC_ARM_REG_R0))
    accepted+=out.value!=65535;rejected+=out.value==65535
out=C.c_uint32(0xcccccccc)
for buf,size,count,descriptor in [(None,68,1,0),(C.create_string_buffer(bytes(68)),67,1,0),(None,0,33,0),(None,0,0,512)]:
    assert not fn(buf,size,count,0,0,descriptor,C.byref(out)) and out.value==0xcccccccc
assert accepted and rejected
report=dict(result='PASS',original_ARM_cases=len(cases),accepted=accepted,rejected=rejected,invalid_inputs_preserve_output=4,
    scope='Original oriented world-ring boundary primitive, including boundaries, empty rings and arithmetic wrap. Complete spatial selection and fallback are not implemented.')
(root/'visibility-contains-tests.json').write_text(json.dumps(report,indent=2));print(report)
