from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x03000000,0x10000),(0x02000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);u.mem_map(0x08000000,len(rom));u.mem_write(0x08000000,rom);u.mem_map(0x02010000,0x40000)
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
cases=children=replacements=failures=0
for group in json.loads((root/'visibility-builder-coverage.json').read_text())['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();stride=88+0x48000;header=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def memory(addr,n):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+n<=base+len(data):return data[addr-base:addr-base+n]
   raise ValueError((hex(addr),n))
  state=memory(header[4],256);table=struct.unpack_from('<I',state,0x60)[0];dt=struct.unpack_from('<I',state,0x14)[0]
  for index in range(struct.unpack_from('<H',state,0xee)[0]):
   region=struct.unpack('<H',memory(table+index*16,2))[0];descriptor=memory(dt+region*48,48);replace=bool(descriptor[0x12]&8)
   u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:]);u.mem_write(0x02040000,state);u.mem_write(0x02040100,descriptor);u.mem_write(0x02000200,struct.pack('<H',99));calls.clear()
   for reg,val in [(UC_ARM_REG_R0,0xffff0000),(UC_ARM_REG_LR,65535),(UC_ARM_REG_R5,0x02040000),(UC_ARM_REG_R6,0x02000200),(UC_ARM_REG_R7,0x02040100),(UC_ARM_REG_R8,0),(UC_ARM_REG_SP,0x03007d00)]:u.reg_write(reg,val)
   u.emu_start(0x030028d0 if replace else 0x03002abc,0x03002930 if replace else 0x03002aec,count=10000)
   reads=[]
   @Reader
   def retained(ctx,addr,dst,n):reads.append((addr,n));C.memmove(dst,memory(addr,n),n);return 1
   st=C.create_string_buffer(state);desc=C.create_string_buffer(descriptor);out=(C.c_uint32*512)();n=C.c_uint();mode=C.c_uint()
   assert fn(st,desc,retained,None,out,512,C.byref(n),C.byref(mode))==1
   assert list(out[:n.value])==calls and mode.value==replace
   children+=n.value;replacements+=replace;cases+=1
   if n.value:
    count=n.value;out=(C.c_uint32*512)(*[123]*512);n=C.c_uint(99);mode=C.c_uint(99)
    assert not fn(st,desc,retained,None,out,count-1,C.byref(n),C.byref(mode)) and list(out)==[123]*512 and n.value==99 and mode.value==99
    failures+=1
# Explicit late-read failure after a successful first link must not publish.
state=bytearray(256);struct.pack_into('<I',state,0x14,0x02001000);descriptor=bytearray(48);descriptor[0x12]=8;struct.pack_into('<H',descriptor,0x24,1)
for failed_read in [1,2]:
 seen=[0]
 @Reader
 def fail(ctx,addr,dst,size):
  seen[0]+=1
  if seen[0]==failed_read:return 0
  child=bytearray(48);struct.pack_into('<H',child,0x24,2);C.memmove(dst,bytes(child),48);return 1
 out=(C.c_uint32*512)(*[123]*512);n=C.c_uint(99);mode=C.c_uint(99)
 assert not fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(descriptor)),fail,None,out,512,C.byref(n),C.byref(mode)) and list(out)==[123]*512 and n.value==99 and mode.value==99
 failures+=1
report=dict(result='PASS',captured_region_link_cases=cases,children_enumerated=children,replacement_regions=replacements,atomic_capacity_or_read_failures=failures,scope='Captured link scheduling fragments with recursive leaves stubbed; no full recursion/rendering.')
(root/'visibility-region-links-captured-tests.json').write_text(json.dumps(report,indent=2));print(report)
