"""Native8021F08 height against original Thumb, with synthetic owned geometry."""
from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=d.nf_object_ground_height;fn.argtypes=[C.c_void_p,C.c_uint,C.c_int32,C.c_int32,Read,C.c_void_p,C.c_void_p]
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
rng=random.Random(0x21f08);fallbacks=planes=atomic=0
for trial in range(600):
 state=bytearray(256);struct.pack_into('<I',state,16,0x02008000);struct.pack_into('<I',state,20,0x02001000);struct.pack_into('<I',state,28,0x02009000);descs=bytearray(96)
 fallback=trial%3==0;index=1 if fallback else 0;fallbacks+=fallback
 struct.pack_into('<H',descs,32,1 if fallback else 65535)
 base=index*48;struct.pack_into('<H',descs,base+8,1);struct.pack_into('<H',descs,base+10,0 if trial%2 else 65535);struct.pack_into('<h',descs,base+38,rng.randrange(-100,101))
 normals=[rng.randrange(-20000,20001),rng.choice([0,1,-1,127,-32768,32767,rng.randrange(-20000,20001)]),rng.randrange(-20000,20001)];struct.pack_into('<3h',descs,base+20,*normals)
 vertex=bytearray(68);struct.pack_into('<2i',vertex,0,rng.randrange(-30000,30001),rng.randrange(-30000,30001));struct.pack_into('<h',vertex,56,rng.randrange(-100,101));plane=bytearray(20);struct.pack_into('<h',plane,6,rng.randrange(-100,101));struct.pack_into('<3h',plane,12,*normals);planes+=trial%2
 for a,b in [(0x02000000,state),(0x02001000,descs),(0x02008000,vertex),(0x02009000,plane)]:u.mem_write(a,bytes(b))
 x,z=rng.randrange(-40000,40001),rng.randrange(-40000,40001)
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0),(UC_ARM_REG_R2,x&0xffffffff),(UC_ARM_REG_R3,z&0xffffffff),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x08021f09,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 out=C.c_int32(123);assert fn(bytes(state),0,x,z,read,None,C.byref(out));assert out.value&0xffffffff==u.reg_read(UC_ARM_REG_R0),(trial,out.value,u.reg_read(UC_ARM_REG_R0))
@Read
def unavailable(ctx,a,out,n):return 0
out=C.c_int32(123);assert not fn(bytes(state),0,0,0,unavailable,None,C.byref(out)) and out.value==123;atomic+=1
assert not fn(bytes(state),512,0,0,read,None,C.byref(out)) and out.value==123;atomic+=1
report=dict(result='PASS',original_thumb_cases=600,neighbor_fallback_cases=fallbacks,external_plane_cases=planes,atomic_rejections=atomic,scope='World-plane Q8 height only; selector12 state/sound/projection dependencies not implemented.')
(p/'object-ground-tests.json').write_text(json.dumps(report,indent=2));print(report)
