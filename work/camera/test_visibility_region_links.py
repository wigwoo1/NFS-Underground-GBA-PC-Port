from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x03000000,0x10000),(0x02000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_region_links
fn.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
calls=[]
def hook(uc,pc,size,ctx):
 if pc==0x030027f0:
  calls.append(struct.unpack('<H',uc.mem_read(0x02000200,2))[0]);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 if pc==0x03002b68:uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
@Reader
def read(ctx,addr,dst,n):C.memmove(dst,bytes(u.mem_read(addr,n)),n);return 1
cases=0
for replace in [0,1]:
 for length in range(33):
  state=bytearray(256);struct.pack_into('<I',state,0x14,0x02001000)
  descriptor=bytearray(48);descriptor[0x12]=8 if replace else 0
  struct.pack_into('<H',descriptor,0x24 if replace else 6,1 if length else 65535)
  for i in range(1,length+1):
   child=bytearray(48);struct.pack_into('<H',child,0x24,i+1 if i<length else 65535);u.mem_write(0x02001000+i*48,bytes(child))
  u.mem_write(0x02000000,bytes(state));u.mem_write(0x02000100,bytes(descriptor));u.mem_write(0x02000200,struct.pack('<H',99));calls.clear()
  for reg,val in [(UC_ARM_REG_R0,0xffff0000),(UC_ARM_REG_LR,65535),(UC_ARM_REG_R5,0x02000000),(UC_ARM_REG_R6,0x02000200),(UC_ARM_REG_R7,0x02000100),(UC_ARM_REG_R8,0),(UC_ARM_REG_SP,0x03007d00)]:u.reg_write(reg,val)
  u.emu_start(0x030028d0 if replace else 0x03002abc,0x03002930 if replace else 0x03002aec,count=10000)
  out=(C.c_uint32*512)();n=C.c_uint();mode=C.c_uint()
  assert fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(descriptor)),read,None,out,512,C.byref(n),C.byref(mode))==1
  assert list(out[:n.value])==calls and mode.value==replace and struct.unpack('<H',u.mem_read(0x02000200,2))[0]==99
  cases+=1
# Cycle must fail without publishing partial children.
descriptor[0x12]=8;struct.pack_into('<H',descriptor,0x24,1);child=bytearray(48);struct.pack_into('<H',child,0x24,1);u.mem_write(0x02001030,bytes(child))
out=(C.c_uint32*512)(*[123]*512);n=C.c_uint(99);mode=C.c_uint(99)
assert not fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(descriptor)),read,None,out,512,C.byref(n),C.byref(mode)) and list(out)==[123]*512 and n.value==99 and mode.value==99
report=dict(result='PASS',original_ARM_link_cases=cases,cycle_rejected_atomically=True,scope='Child link order and own-draw replacement policy only; child calls stubbed, not full recursive rendering.')
(root/'visibility-region-links-tests.json').write_text(json.dumps(report,indent=2));print(report)
