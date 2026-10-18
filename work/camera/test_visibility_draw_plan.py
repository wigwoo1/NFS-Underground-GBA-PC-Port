from pathlib import Path
import ctypes as C,json,struct,random,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);calls=[]
def hook(cpu,address,size,ctx):
 if address==0x03005224:cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 if address==0x030027f0:
  assert cpu.reg_read(UC_ARM_REG_R0)==0x02000000
  offset=cpu.reg_read(UC_ARM_REG_R1)-0x02001000;assert offset%16==0
  calls.append((offset//16,cpu.reg_read(UC_ARM_REG_R2)))
  cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_draw_plan
fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
coverage=json.loads((root/'visibility-builder-coverage.json').read_text());fixtures=[]
for group in coverage['cases']:
 for item in group['samples']:
  blob=(root/'visibility-corpus'/item['file']).read_bytes();stride=88+0x48000;h=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def mem(addr,n):
   off=addr-0x02000000 if addr<0x03000000 else 0x40000+addr-0x03000000
   return ram[off:off+n]
  state=mem(h[4],256);count=struct.unpack_from('<H',state,0xee)[0];queue=mem(struct.unpack_from('<I',state,0x60)[0],320)
  fixtures.append((count,queue))
rng=random.Random(0x4d5c)
for count in range(21):
 for mode in [0,8,0x80,0x88,None]:
  q=bytearray(320)
  for i in range(count):struct.pack_into('<H',q,i*16+10,rng.randrange(65536) if mode is None else mode)
  fixtures.append((count,bytes(q)))
failures=total=0
for count,queue in fixtures:
 calls.clear();u.mem_write(0x02001000,queue);u.mem_write(0x02000060,struct.pack('<I',0x02001000));u.mem_write(0x020000ee,struct.pack('<H',count))
 for reg,value in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,value)
 u.emu_start(0x03004d5c,0x03006000,count=5000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 result=(C.c_uint32*80)(*([0xcccccccc]*80));n=C.c_uint(0xdddddddd);q=C.create_string_buffer(queue)
 assert fn(q,count,result,40,C.byref(n))
 assert list(zip(list(result)[:n.value*2:2],list(result)[1:n.value*2:2]))==calls
 assert q.raw[:320]==queue;total+=n.value
 if n.value:
  result=(C.c_uint32*80)(*([0xcccccccc]*80));n=C.c_uint(0xdddddddd)
  assert not fn(q,count,result,len(calls)-1,C.byref(n))
  assert n.value==0xdddddddd and list(result)==[0xcccccccc]*80;failures+=1
report=dict(result='PASS',captured_queue_cases=69,synthetic_flag_and_count_cases=len(fixtures)-69,original_dispatch_calls=total,capacity_failures_atomic=failures,
 scope='Original outer dispatcher call order/flags matched with draw-scratch clear and region-draw leaves stubbed. Leaf world/object draw generation is not implemented by this plan.')
(root/'visibility-draw-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
