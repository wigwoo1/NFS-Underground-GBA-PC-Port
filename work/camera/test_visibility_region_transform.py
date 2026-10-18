from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_region_transform
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_size_t]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
coverage=json.loads((root/'visibility-builder-coverage.json').read_text());accepted=far=failures=materials=0
for group in coverage['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();stride=88+0x48000;h=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def memory(addr,n):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+n<=base+len(data):return data[addr-base:addr-base+n]
   raise ValueError((hex(addr),n))
  state=memory(h[4],256);table=struct.unpack_from('<I',state,0x60)[0];regions=struct.unpack_from('<H',state,0xee)[0]
  for index in range(regions):
   region=struct.unpack('<H',memory(table+index*16,2))[0];da=struct.unpack_from('<I',state,0x14)[0]+region*48
   descriptor=memory(da,48);first,count=struct.unpack_from('<2H',descriptor)
   va=struct.unpack_from('<I',state,0x10)[0]+first*68;vertices=memory(va,count*68)
   scratch_address=struct.unpack_from('<I',state,0x68)[0];initial=memory(scratch_address,count*52)
   materials+=sum(struct.unpack_from('<H',vertices,i*68+0x2a)[0]!=65535 for i in range(count))
   u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:])
   for reg,val in [(UC_ARM_REG_R0,h[4]),(UC_ARM_REG_R1,da),(UC_ARM_REG_R2,va),(UC_ARM_REG_R3,count),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
   u.emu_start(0x03000d48,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
   calls=[]
   @Reader
   def read(ctx,addr,dst,n):calls.append((addr,n));C.memmove(dst,memory(addr,n),n);return 1
   out=C.create_string_buffer(initial);v=C.create_string_buffer(vertices);st=C.create_string_buffer(state)
   result=fn(st,v,len(vertices),count,read,None,out,len(initial))
   assert result==u.reg_read(UC_ARM_REG_R0),(sample['file'],index,result)
   assert out.raw[:len(initial)]==bytes(u.mem_read(scratch_address,len(initial)))
   assert st.raw[:256]==state and v.raw[:len(vertices)]==vertices
   accepted+=result==1;far+=result==0
   for failure in range(len(calls)):
    seen=[0]
    @Reader
    def fail(ctx,addr,dst,n):
     seen[0]+=1
     if seen[0]==failure+1:return 0
     C.memmove(dst,memory(addr,n),n);return 1
    out=C.create_string_buffer(initial)
    assert fn(st,v,len(vertices),count,fail,None,out,len(initial))==-1 and out.raw[:len(initial)]==initial
    failures+=1
synthetic=0
for depth in [64,0x5fff,0x6000,-100]:
 for use_material in [False,True]:
  state=bytearray(256);struct.pack_into('<I',state,0x18,0x02002000);struct.pack_into('<I',state,0x54,0x02001000);struct.pack_into('<I',state,0x68,0x02003000)
  matrix=struct.pack('<12I',16384,0,0,0,16384,0,0,0,16384,0,100,0)
  material=bytearray(32);struct.pack_into('<2h',material,0,-17,3);struct.pack_into('<2h',material,8,-9,11)
  vertices=bytearray(3*68)
  for i in range(3):
   struct.pack_into('<2I',vertices,i*68,(i*23-10)&0xffffffff,depth&0xffffffff)
   struct.pack_into('<4H',vertices,i*68+8,0xfff0,16,32,0xffff)
   struct.pack_into('<H',vertices,i*68+0x2a,0 if use_material else 65535)
   vertices[i*68+60:i*68+62]=bytes([i*70,255-i*20])
  initial=bytes([0xa5])*156
  for address,data in [(0x02000000,state),(0x02001000,matrix),(0x02002000,material),(0x02003000,initial),(0x02004000,vertices)]:u.mem_write(address,bytes(data))
  for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R2,0x02004000),(UC_ARM_REG_R3,3),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
  u.emu_start(0x03000d48,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
  @Reader
  def read_synthetic(ctx,addr,dst,n):C.memmove(dst,bytes(u.mem_read(addr,n)),n);return 1
  out=C.create_string_buffer(initial)
  result=fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(vertices)),len(vertices),3,read_synthetic,None,out,len(initial))
  assert result==u.reg_read(UC_ARM_REG_R0) and out.raw[:156]==bytes(u.mem_read(0x02003000,156))
  synthetic+=1;accepted+=result==1;far+=result==0
assert far>0
report=dict(result='PASS',original_ARM_region_cases=accepted+far,synthetic_material_and_depth_cases=synthetic,completed_rings=accepted,far_depth_stops=far,material_offset_vertices=materials,atomic_read_failures=failures,
 scope='Original region geometry scratch transform, heights, intensity seeds and cyclic endpoints. No wall/road command emission or live drawing.')
(root/'visibility-region-transform-tests.json').write_text(json.dumps(report,indent=2));print(report)
