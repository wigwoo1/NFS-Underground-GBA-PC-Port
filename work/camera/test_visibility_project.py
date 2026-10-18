from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
def stop(cpu,address,length,context):cpu.emu_stop()
for address in (0x03002f60,0x03002f70):u.hook_add(UC_HOOK_CODE,stop,begin=address,end=address)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_project;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);r=random.Random(0x2d20);results={0:0,1:0,2:0};clips={0:0,8:0,16:0}
cases=[]
for i in range(1800):
    cases.append([r.randrange(-40000,40000),r.randrange(-4000,25000),r.randrange(-40000,40000),r.randrange(-4000,25000),r.choice([1,64,128,512]),r.randrange(-200,300),r.choice([128,256,384,65535,0x7fffffff]),i%2])
for z in (63,64,65,24576,24577):cases.append([-100,z,100,100,64,120,256,0])
for p in cases:
    u.mem_write(0x02000008,struct.pack('<h',p[5]));u.mem_write(0x02000010,struct.pack('<I',p[4]))
    u.mem_write(0x03007e34,struct.pack('<I',p[6]));u.mem_write(0x03007e64,struct.pack('<I',p[7]))
    for reg,v in [(UC_ARM_REG_R5,p[0]),(UC_ARM_REG_R10,p[1]),(UC_ARM_REG_R6,p[2]),(UC_ARM_REG_R8,p[3]),(UC_ARM_REG_R2,0x02000000),(UC_ARM_REG_SP,0x03007e00)]:u.reg_write(reg,v&0xffffffff)
    u.emu_start(0x03002d20,0x03002e18,count=1000)
    expected={0x03002e18:1,0x03002f60:0,0x03002f70:2}[u.reg_read(UC_ARM_REG_PC)]
    out=(C.c_uint32*5)(*([0xdeadbeef]*5));result=fn((C.c_int32*8)(*p),table,out);assert result==expected,(p,result,expected)
    results[result]+=1
    if result==1:
        actual=[u.reg_read(reg) for reg in [UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R10,UC_ARM_REG_R8]]+[struct.unpack('<I',u.mem_read(0x03007e04,4))[0]]
        assert list(out)==actual,(p,list(out),actual);clips[out[4]]+=1
    else:assert list(out)==[0xdeadbeef]*5
out=(C.c_uint32*5)(1,2,3,4,5)
assert fn((C.c_int32*8)(0,-40000,100,100,64,120,256,0),table,out)==-1 and list(out)==[1,2,3,4,5]
report=dict(result='PASS',original_ARM_cases=len(cases),outcomes=results,projected_clip_flags=clips,invalid_denominator_preserves_output=True,
            scope='Original near clipping, far-depth stop and fixed-point projection. World transform and live renderer integration remain separate.')
(root/'visibility-project-tests.json').write_text(json.dumps(report,indent=2));print(report)
