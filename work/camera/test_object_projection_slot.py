"""Original projection allocator versus native, with explicit matrix builder seam."""
from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);global_address=struct.unpack_from('<I',rom,0x23a0c)[0]
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);Build=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p);fn=d.nf_object_projection_slot;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,Build,C.c_void_p]
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
calls=[];native_calls=[]
def result(camera,obj,old):return bytes(a^b for a,b in zip(old,camera))
def hook(cpu,pc,n,ctx):
 if pc==0x08022c24:
  camera=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R0),48));obj=bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),164));dest=cpu.reg_read(UC_ARM_REG_R2);old=bytes(cpu.mem_read(dest,48));calls.append((camera,obj,old));cpu.mem_write(dest,result(camera,obj,old));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
@Build
def build(ctx,camera,obj,out):
 c,o,old=C.string_at(camera,48),C.string_at(obj,164),C.string_at(out,48);native_calls.append((c,o,old));C.memmove(out,result(c,o,old),48);return 1
rng=random.Random(0x239c0);builds=overflows=0
for trial in range(350):
 state=bytearray(256);struct.pack_into('<I',state,84,0x02009000);struct.pack_into('<I',state,252,0x0200b000);obj=bytearray(rng.randbytes(164));struct.pack_into('<h',obj,54,0 if trial%5==0 else -1);flags=struct.unpack_from('<H',obj,10)[0];struct.pack_into('<H',obj,10,(flags|4) if trial%3 else flags&~4);count=[0,1,61,62,63,64,100,0xffffffff][trial%8];scratch=rng.randbytes(64*48);camera=rng.randbytes(48)
 for a,b in [(0x02000000,state),(0x0200a000,obj),(0x02009000,camera),(0x0200b000,scratch),(global_address,struct.pack('<I',count))]:u.mem_write(a,bytes(b))
 calls.clear();native_calls.clear()
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x0200a000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x080239c1,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 no=C.create_string_buffer(bytes(obj),164);ns=C.create_string_buffer(scratch,len(scratch));nc=C.c_uint32(count);assert fn(bytes(state),no,C.byref(nc),ns,read,None,build,None)
 assert no.raw==bytes(u.mem_read(0x0200a000,164)) and ns.raw==bytes(u.mem_read(0x0200b000,len(scratch))) and nc.value==struct.unpack('<I',bytes(u.mem_read(global_address,4)))[0] and calls==native_calls,trial
 builds+=len(calls);overflows+=nc.value!=count and no.raw[136]==255
obj=bytearray(164);struct.pack_into('<h',obj,54,1);struct.pack_into('<H',obj,10,4);no=C.create_string_buffer(bytes(obj),164);ns=C.create_string_buffer(scratch,len(scratch));nc=C.c_uint32(0);assert not fn(bytes(state),no,C.byref(nc),ns,read,None,Build(),None) and no.raw==bytes(obj) and ns.raw==scratch and nc.value==0
@Build
def reject_build(ctx,camera,obj,out):
 C.memset(out,0x5a,48);return 0
@Read
def reject_read(ctx,a,out,n):return 0
for reader,builder in [(read,reject_build),(reject_read,build)]:
 assert not fn(bytes(state),no,C.byref(nc),ns,reader,None,builder,None) and no.raw==bytes(obj) and ns.raw==scratch and nc.value==0
report=dict(result='PASS',original_thumb_cases=350,matrix_adapter_calls=builds,overflow_sentinel_cases=overflows,atomic_rejections=3,scope='Projection slot/flag allocator only; matrix builder deliberately stubbed, camera/object/destination verified. Actual rotation matrix construction remains incomplete.')
(p/'object-projection-slot-tests.json').write_text(json.dumps(report,indent=2));print(report)
