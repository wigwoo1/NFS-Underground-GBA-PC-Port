from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x10000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_wall_prepare
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p]
rng=random.Random(1958);failures=0
for case in range(512):
 state=bytearray(256);struct.pack_into('<I',state,0x20,0x02002000);struct.pack_into('<I',state,0x48,0x02003000);struct.pack_into('<I',state,0x18,0x02004000)
 source=bytearray(rng.randbytes(68));nxt=bytearray(rng.randbytes(68));material=bytearray(rng.randbytes(32));animation=rng.randbytes(8);offsets=rng.randbytes(64);initial=rng.randbytes(52)
 struct.pack_into('<H',source,0x2c,0);struct.pack_into('<H',material,0,0)
 struct.pack_into('<H',material,0x1a,[0,1,8,16,32,33,257,65535][case%8])
 struct.pack_into('<H',source,0x2a,0 if case&1 else 65535);struct.pack_into('<H',nxt,0x2a,1 if case&2 else 65535)
 bases=(C.c_uint32*2)(rng.getrandbits(32),rng.getrandbits(32))
 for addr,data in [(0x02000000,state),(0x02000100,source),(0x02000200,nxt),(0x02000300,initial),(0x02002000,material),(0x02003000,animation),(0x02004000,offsets)]:u.mem_write(addr,bytes(data))
 sp=0x02001000
 for off,val in [(0x70,0x02000000),(0x60,0x02000200),(0x3c,bases[0]),(0x38,bases[1])]:u.mem_write(sp+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R7,0x02000100),(UC_ARM_REG_R5,0x02000300),(UC_ARM_REG_SP,sp)]:u.reg_write(reg,val)
 u.emu_start(0x03001958,0x03001b0c,count=200);assert u.reg_read(UC_ARM_REG_PC)==0x03001b0c
 expected=[u.reg_read(UC_ARM_REG_R9),u.reg_read(UC_ARM_REG_R10),struct.unpack('<I',u.mem_read(sp+12,4))[0],struct.unpack('<I',u.mem_read(sp+8,4))[0]]
 calls=[]
 @Reader
 def read(ctx,addr,out,n):calls.append((addr,n));C.memmove(out,bytes(u.mem_read(addr,n)),n);return 1
 st=C.create_string_buffer(bytes(state));src=C.create_string_buffer(bytes(source));nx=C.create_string_buffer(bytes(nxt));out=C.create_string_buffer(initial);h=(C.c_uint32*4)()
 assert fn(st,src,nx,bases,read,None,h,out)==1
 assert list(h)==expected and out.raw[:52]==bytes(u.mem_read(0x02000300,52)),case
 for failure in range(len(calls)):
  seen=[0]
  @Reader
  def fail(ctx,addr,out,n):
   seen[0]+=1
   if seen[0]==failure+1:return 0
   C.memmove(out,bytes(u.mem_read(addr,n)),n);return 1
  out=C.create_string_buffer(initial);h=(C.c_uint32*4)(1,2,3,4)
  assert fn(st,src,nx,bases,fail,None,h,out)==0 and list(h)==[1,2,3,4] and out.raw[:52]==initial
  failures+=1
report=dict(result='PASS',original_ARM_synthetic_cases=512,atomic_read_failures=failures,scope='Resolved wall material/animation, endpoint height offsets and UV setup; no clipping/projection/live drawing.')
(root/'visibility-wall-prepare-tests.json').write_text(json.dumps(report,indent=2));print(report)
