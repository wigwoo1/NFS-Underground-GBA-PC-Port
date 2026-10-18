from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x03000000,0x10000),(0x02000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_wall_draw_plan
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint32,Reader,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
rng=random.Random(264);calls=[]
def half(a):return struct.unpack('<H',u.mem_read(a,2))[0]
def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def hook(uc,pc,size,ctx):
 if pc==0x03000304:
  context=uc.reg_read(UC_ARM_REG_R0);calls.append([(uc.reg_read(UC_ARM_REG_R6)-0x02001000)//68,uc.reg_read(UC_ARM_REG_R3),word(context+40),half(context+36),half(context+38),uc.reg_read(UC_ARM_REG_R2)])
  uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook,begin=0x03000304,end=0x03000304)
total=cases=0
for trial in range(256):
 count=trial%32+1;state=bytearray(256)
 for off,val in [(0,0x08000000),(0x10,0x02001000),(0x14,0x02000100),(0x18,0x02005000),(0x20,0x02004000),(0x48,0x02006000),(0x68,0x02002000)]:struct.pack_into('<I',state,off,val)
 struct.pack_into('<2H',state,0xe6,0,160)
 descriptor=bytearray(48);struct.pack_into('<2H',descriptor,0,0,count)
 vertices=bytearray(rng.randbytes(count*68));scratch=bytearray(rng.randbytes(count*52));materials=bytearray(rng.randbytes(32*16));animations=bytearray(rng.randbytes(8*4));offsets=rng.randbytes(32*4)
 for i in range(count):
  struct.pack_into('<3H',vertices,i*68+0x2a,rng.choice([65535,0,1,2,3]),rng.randrange(8),rng.getrandbits(16))
  struct.pack_into('<H',scratch,i*52+0x30,rng.randrange(4)*2)
 for i in range(16):struct.pack_into('<H',materials,i*32,rng.randrange(4))
 for i in range(4):struct.pack_into('<H',animations,i*8+2,rng.randrange(4))
 for addr,data in [(0x02000000,state),(0x02000100,descriptor),(0x02000200,bytes(16)),(0x02001000,vertices),(0x02002000,scratch),(0x02004000,materials),(0x02005000,offsets),(0x02006000,animations)]:u.mem_write(addr,bytes(data))
 mask=0
 for second in [0,None]:
  second=mask if second is None else second;calls.clear()
  for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02000200),(UC_ARM_REG_R2,0x02000300),(UC_ARM_REG_R3,second),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
  u.emu_start(0x0300264c,0x03006000,count=20000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
  @Reader
  def read(ctx,addr,dst,n):C.memmove(dst,bytes(u.mem_read(addr,n)),n);return 1
  out=(C.c_uint32*(32*6))();n=C.c_uint();deferred=C.c_uint32()
  assert fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(vertices)),count,C.create_string_buffer(bytes(scratch)),second,read,None,out,32,C.byref(n),C.byref(deferred))==1
  assert [list(out[i*6:i*6+6]) for i in range(n.value)]==calls,(trial,second)
  assert deferred.value==u.reg_read(UC_ARM_REG_R0),(trial,second,'mask')
  mask=deferred.value;total+=len(calls);cases+=1
report=dict(result='PASS',synthetic_original_dispatches=cases,raster_leaf_calls=total,scope='Wall filtering, deferred mask and animated material/texture command resolution; raster leaf stubbed.')
(root/'visibility-wall-draw-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
