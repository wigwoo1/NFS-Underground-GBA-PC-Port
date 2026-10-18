from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for addr,size in [(0x03000000,0x10000),(0x02000000,0x10000),(0x08000000,len(rom))]:u.mem_map(addr,size)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);u.mem_write(0x08000000,rom)
fn=C.CDLL(str((root/'visibility-probe-wide.dll').resolve())).nfs_visibility_wall_clip
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_uint,C.c_uint,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
rng=random.Random(1638);counts=[0,0,0,0]
for case in range(1600):
 near=[1,64,128,1024][case%4];z0=rng.randrange(-8000,8000);z1=rng.randrange(-8000,8000)
 if case%10==0:z0=near
 if case%11==0:z1=near
 flags=rng.getrandbits(16);region=case%3
 initial=bytearray(rng.randbytes(52));struct.pack_into('<2h',initial,4,z0,z1)
 h0=[rng.getrandbits(32) for _ in range(4)];a0=[rng.getrandbits(32) for _ in range(4)]
 source=bytearray(68);struct.pack_into('<H',source,0x2e,flags);descriptor=bytearray(48);descriptor[0x12]=region
 for addr,data in [(0x02000000,initial),(0x02000100,source),(0x02000200,descriptor)]:u.mem_write(addr,bytes(data))
 sp=0x02001000
 for off,val in [(0x58,near),(0x5c,0),(0x68,0x02000200),(0xc,h0[2]),(8,h0[3]),(0x30,a0[0]),(0x28,a0[1]),(0x2c,a0[2]),(0x24,a0[3])]:u.mem_write(sp+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R4,z0&0xffffffff),(UC_ARM_REG_R12,z1&0xffffffff),(UC_ARM_REG_R5,0x02000000),(UC_ARM_REG_R7,0x02000100),(UC_ARM_REG_R9,h0[0]),(UC_ARM_REG_R10,h0[1]),(UC_ARM_REG_SP,sp)]:u.reg_write(reg,val)
 u.emu_start(0x03001b0c,0x03001ca0,count=1000);assert u.reg_read(UC_ARM_REG_PC)==0x03001ca0
 def w(off):return struct.unpack('<I',u.mem_read(sp+off,4))[0]
 expectedh=[u.reg_read(UC_ARM_REG_R9),u.reg_read(UC_ARM_REG_R10),w(12),w(8)]
 expecteda=[w(0x30),w(0x28),w(0x2c),w(0x24)]
 out=C.create_string_buffer(bytes(initial));h=(C.c_uint32*4)(*h0);a=(C.c_uint32*4)(*a0)
 result=fn(out,h,a,near,flags,region,recip)
 assert result==1-w(0x5c),(case,result,w(0x5c))
 assert out.raw[:52]==bytes(u.mem_read(0x02000000,52)) and list(h)==expectedh and list(a)==expecteda,case
 counts[(z0<near)*2+(z1<near)]+=1
# Crossing with reciprocal index outside supported table must be atomic.
initial=bytearray(52);struct.pack_into('<2h',initial,4,-32768,32767)
out=C.create_string_buffer(bytes(initial));h=(C.c_uint32*4)(1,2,3,4);a=(C.c_uint32*4)(5,6,7,8)
assert fn(out,h,a,64,128,1,recip)==-1 and out.raw[:52]==initial and list(h)==[1,2,3,4] and list(a)==[5,6,7,8]
report=dict(result='PASS',original_ARM_synthetic_cases=1600,front_front=counts[0],front_behind=counts[1],behind_front=counts[2],behind_behind=counts[3],invalid_reciprocal_range_atomic=True,scope='Near-plane wall clipping and attribute interpolation only; no projection or live rendered gameplay.')
(root/'road-near-original-arm-tests.json').write_text(json.dumps(report,indent=2));print(report)
