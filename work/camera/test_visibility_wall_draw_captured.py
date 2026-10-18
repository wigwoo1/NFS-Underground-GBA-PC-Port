from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_wall_draw_plan
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint32,Reader,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
u.mem_map(0x02040000,0x10000)
calls=[]
def hook(uc,pc,size,ctx):
 context=uc.reg_read(UC_ARM_REG_R0)
 def word(a):return struct.unpack('<I',uc.mem_read(a,4))[0]
 def half(a):return struct.unpack('<H',uc.mem_read(a,2))[0]
 calls.append([(uc.reg_read(UC_ARM_REG_R6)-va)//68,uc.reg_read(UC_ARM_REG_R3),word(context+40),half(context+36),half(context+38),uc.reg_read(UC_ARM_REG_R2)])
 uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook,begin=0x03000304,end=0x03000304)
cases=leaves=failures=capacity_failures=0
for group in json.loads((root/'visibility-builder-coverage.json').read_text())['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();stride=88+0x48000;header=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def memory(addr,n):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+n<=base+len(data):return data[addr-base:addr-base+n]
   raise ValueError((hex(addr),n))
  state=bytearray(memory(header[4],256));table=struct.unpack_from('<I',state,0x60)[0]
  for index in range(struct.unpack_from('<H',state,0xee)[0]):
   record=memory(table+index*16,16);region=struct.unpack_from('<H',record)[0];da=struct.unpack_from('<I',state,0x14)[0]+region*48;descriptor=memory(da,48)
   first,count=struct.unpack_from('<2H',descriptor);va=struct.unpack_from('<I',state,0x10)[0]+first*68;vertices=memory(va,count*68)
   state[0xe2:0xea]=record[2:10];scratchaddr=struct.unpack_from('<I',state,0x68)[0]
   u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:]);u.mem_write(header[4],bytes(state))
   def run(start,regs):
    for reg,val in regs+[(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
    u.emu_start(start,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
   run(0x03000d48,[(UC_ARM_REG_R0,header[4]),(UC_ARM_REG_R1,da),(UC_ARM_REG_R2,va),(UC_ARM_REG_R3,count)])
   assert u.reg_read(UC_ARM_REG_R0)==1
   initial=bytes(u.mem_read(scratchaddr,count*52))
   surfaceaddr=struct.unpack_from("<I",state,0x6c)[0];surface_initial=bytes(u.mem_read(surfaceaddr,64*24));stream=C.create_string_buffer(surface_initial)
   queue_flags=struct.unpack_from("<H",record,10)[0]
   u.mem_write(0x03007d00,struct.pack('<I',table+index*16))
   run(0x03001800,[(UC_ARM_REG_R0,header[4]),(UC_ARM_REG_R1,va),(UC_ARM_REG_R2,count),(UC_ARM_REG_R3,da)])
   scratch=bytes(u.mem_read(scratchaddr,count*52));mask=0
   for pass_index in range(2):
    calls.clear();second=mask
    run(0x0300264c,[(UC_ARM_REG_R0,header[4]),(UC_ARM_REG_R1,table+index*16),(UC_ARM_REG_R2,0x02040000),(UC_ARM_REG_R3,second)])
    accesses=[]
    @Reader
    def read(ctx,addr,dst,n):accesses.append((addr,n));C.memmove(dst,memory(addr,n),n);return 1
    st=C.create_string_buffer(bytes(state));v=C.create_string_buffer(vertices);edge=C.create_string_buffer(scratch);out=(C.c_uint32*192)();n=C.c_uint(99);deferred=C.c_uint32(99)
    assert fn(st,v,count,edge,second,read,None,out,32,C.byref(n),C.byref(deferred))==1
    assert [list(out[i*6:i*6+6]) for i in range(n.value)]==calls,(sample['file'],index,pass_index)
    assert deferred.value==u.reg_read(UC_ARM_REG_R0)
    mask=deferred.value;leaves+=len(calls);cases+=1
    for failure in range(len(accesses)):
     seen=[0]
     @Reader
     def fail(ctx,addr,dst,size):
      seen[0]+=1
      if seen[0]==failure+1:return 0
      C.memmove(dst,memory(addr,size),size);return 1
     out=C.create_string_buffer(b'\xcc'*768);n=C.c_uint(99);d=C.c_uint32(99)
     assert fn(st,v,count,edge,second,fail,None,out,32,C.byref(n),C.byref(d))==0
     assert out.raw[:768]==b'\xcc'*768 and n.value==99 and d.value==99
     failures+=1
    if calls:
     out=C.create_string_buffer(b'\xcc'*768);n=C.c_uint(99);d=C.c_uint32(99)
     assert fn(st,v,count,edge,second,read,None,out,len(calls)-1,C.byref(n),C.byref(d))==0
     assert out.raw[:768]==b'\xcc'*768 and n.value==99 and d.value==99
     capacity_failures+=1
report=dict(result='PASS',captured_region_passes=cases,raster_leaf_calls=leaves,atomic_read_failures=failures,atomic_capacity_failures=capacity_failures,scope='Captured wall dispatch/material resolution, raster leaves stubbed; no pixel comparison or live renderer integration.')
(root/'visibility-wall-draw-captured-tests.json').write_text(json.dumps(report,indent=2));print(report)
