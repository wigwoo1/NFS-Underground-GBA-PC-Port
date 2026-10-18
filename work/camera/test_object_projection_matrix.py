"""Native object projection versus complete original Thumb entry + ARM math, no math stubs."""
from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
# Dispatch code relocation identity: original ARM implementations execute from ROM.
u.mem_write(0x03006c50,struct.pack('<I',0x08071e10-0xe4))
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=d.nf_object_projection_matrix;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p]
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
rng=random.Random(0x22c24);skips=externals=0
for trial in range(700):
 camera=[rng.getrandbits(32) for _ in range(12)] if trial%7==0 else [rng.randint(-16384,16384)&0xffffffff for _ in range(12)]
 obj=bytearray(rng.randbytes(164));flags=(2 if trial%3 else 0)|(32 if trial%4<2 else 0);struct.pack_into('<H',obj,10,flags);struct.pack_into('<I',obj,140,0x0200c000);special=trial%2
 # Include threshold boundary with simple identity orientation.
 if trial<3:
  camera=[16384,0,0,0,16384,0,0,0,16384,0,0,0];struct.pack_into('<i',obj,20,(3499+trial)<<8);struct.pack_into('<H',obj,10,0)
 initial=rng.randbytes(48);external=rng.randbytes(356);cb=struct.pack('<12I',*camera)
 for a,b in [(0x02009000,cb),(0x0200a000,obj),(0x0200b000,initial),(0x0200c000,external),(0x03006768,struct.pack('<I',special))]:u.mem_write(a,bytes(b))
 for reg,val in [(UC_ARM_REG_R0,0x02009000),(UC_ARM_REG_R1,0x0200a000),(UC_ARM_REG_R2,0x0200b000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x08022c25,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 output=C.create_string_buffer(initial,48);assert fn(cb,bytes(obj),output,read,None)
 expected=bytes(u.mem_read(0x0200b000,48));assert output.raw==expected,(trial,struct.unpack('<12i',output.raw),struct.unpack('<12i',expected))
 skips+=expected==initial;externals+=bool(flags&32 and special and expected!=initial)
@Read
def reject(ctx,a,out,n):return 0
struct.pack_into('<H',obj,10,2);output=C.create_string_buffer(initial,48);assert not fn(cb,bytes(obj),output,reject,None) and output.raw==initial
struct.pack_into('<H',obj,10,34);assert not fn(cb,bytes(obj),output,reject,None) and output.raw==initial
report=dict(result='PASS',original_projection_cases=700,unchanged_distance_skips=skips,external_matrix_cases=externals,atomic_rejections=2,scope='Complete original8022C24 entry with original ARM trig/rotation/multiply executed; dispatch relocation points to ROM code, no matrix or trig output stubs. Live installed dispatch and full callback integration not yet verified.')
(p/'object-projection-matrix-tests.json').write_text(json.dumps(report,indent=2));print(report)
