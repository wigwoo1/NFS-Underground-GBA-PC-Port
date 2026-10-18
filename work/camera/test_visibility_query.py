"""Compare composed native point selection with the original Thumb sequence."""
from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_query
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
offset_fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_offset
offset_fn.argtypes=[C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);hits=[0,0,0]
def hook(cpu,address,size,ctx):
    if address==0x08002ce8:hits[2]+=1
    if address==0x08022d78:hits[0]+=1
    if address==0x08002d64:hits[1]+=1
u.hook_add(UC_HOOK_CODE,hook)
coverage=json.loads((root/'visibility-builder-coverage.json').read_text());cases=0;faults=0;opposite_misses=0
for group in coverage['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();h=struct.unpack_from('<22I',blob);ram=blob[88:88+0x48000]
  def memory(address,size):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=address and address+size<=base+len(data):return data[address-base:address-base+size]
   raise ValueError((hex(address),size))
  selected=struct.unpack('<H',memory(0x03005d44,2))[0]
  base_x=struct.unpack('<I',memory(0x03005dd0,4))[0];base_z=struct.unpack('<I',memory(0x030000a0,4))[0]
  camera=struct.unpack('<12I',memory(struct.unpack('<I',memory(h[4]+0x54,4))[0],48))
  identity=[16384,0,0,0,16384,0,0,0,16384,0,0,0]
  for variant,matrix in enumerate([camera,identity,identity[:9]+[100000,0,100000],identity[:9]+[0xfffffc18,0,1000]]):
   bx,bz=(base_x,base_z) if variant<2 else (100000*256,100000*256)
   offset=(C.c_uint32*3)();assert offset_fn((C.c_uint32*12)(*matrix),offset)
   dx,dz=offset[0],offset[2]
   u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:])
   sp=0x03007d00;state=h[4]
   u.mem_write(0x03005dd0,struct.pack('<I',bx));u.mem_write(0x030000a0,struct.pack('<I',bz))
   u.mem_write(sp+0xa4,struct.pack('<I',0x03009200));u.mem_write(0x03009278,struct.pack('<H',17))
   u.mem_write(0x03009000,struct.pack('<12I',*matrix));u.mem_write(sp+0x98,struct.pack('<I',0x03009000))
   for reg,value in [(UC_ARM_REG_R0,bz),(UC_ARM_REG_R1,bx),(UC_ARM_REG_SP,sp),(UC_ARM_REG_R7,state+0xea),(UC_ARM_REG_R8,state+0xc0),(UC_ARM_REG_R9,state+0xc8),(UC_ARM_REG_R10,state),(UC_ARM_REG_R4,sp+0x7c)]:u.reg_write(reg,value)
   u.emu_start(0x08002cb5,0x08002d92,count=200000)
   assert u.reg_read(UC_ARM_REG_PC)==0x08002d92
   reads=[];errors=[]
   @Reader
   def read(ctx,addr,dst,size):
    try:reads.append((addr,size));C.memmove(dst,memory(addr,size),size);return 1
    except Exception as e:errors.append(str(e));return 0
   initial=memory(state,256);s=C.create_string_buffer(initial);out=(C.c_uint32*2)();point=(C.c_uint32*2)(bx,bz);chosen=C.c_uint32(selected);m=(C.c_uint32*12)(*matrix)
   assert fn(s,C.byref(chosen),17,point,m,read,None,out) and not errors,(sample['file'],dx,dz,errors)
   assert list(out)==[u.reg_read(UC_ARM_REG_R7),u.reg_read(UC_ARM_REG_R9)],(sample['file'],dx,dz,list(out))
   assert s.raw[:256]==bytes(u.mem_read(state,256))
   assert chosen.value==struct.unpack("<H",u.mem_read(0x03005d44,2))[0]
   assert bytes(offset)==bytes(u.mem_read(sp+0x7c,12))
   opposite_misses+=out[1]==65535;cases+=1
   # Exercise every distinct read failure in the first captured scene for all offsets.
   if cases<=4:
    for index in range(len(reads)):
     calls=[0]
     @Reader
     def fail(ctx,addr,dst,size):
      calls[0]+=1
      if calls[0]==index+1:return 0
      C.memmove(dst,memory(addr,size),size);return 1
     s=C.create_string_buffer(initial);chosen=C.c_uint32(selected);out=(C.c_uint32*2)(0xcccccccc,0xdddddddd)
     assert not fn(s,C.byref(chosen),17,point,m,fail,None,out)
     assert s.raw[:256]==initial and list(out)==[0xcccccccc,0xdddddddd]
     assert chosen.value==selected
     faults+=1
assert cases==276 and hits[0] and hits[1] and opposite_misses
report=dict(result='PASS',original_Thumb_sequence_cases=cases,original_fallback_calls=hits[0],original_keep_previous_cases=hits[1],opposite_no_match=opposite_misses,atomic_read_failures=faults,base_recovery_cases=hits[2],
 scope='Original 08002CB4..08002D92 versus native base recovery, offset generation and paired selection across 69 captured worlds with four explicit matrix/base fixtures. Recovery source is supplied; later root branching and continuous camera matrices remain separate.')
(root/'visibility-query-tests.json').write_text(json.dumps(report,indent=2));print(report)
