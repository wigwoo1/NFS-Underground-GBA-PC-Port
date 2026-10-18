"""Execute the original model's indexed ARM span, including zero texels."""
from pathlib import Path
import sys,struct,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');code=(p/'live-multimodel-baseline-iwram.bin').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for base,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000)]:u.mem_map(base,size)
u.mem_write(0x03000000,code)
for offset,value in [(0x5a30,3),(0x5a34,0),(0x5a38,0),(0x5a3c,0),(0x5a40,0)]:
 address=struct.unpack_from('<I',code,offset)[0]
 assert 0x03000000<=address<0x03008000
 u.mem_write(address,struct.pack('<I',value))
cases=0
for index in [0,1,127,255]:
 for odd in [0,1]:
  for count in range(1,18):
   u.mem_write(0x02001000,bytes([index])*64)
   u.mem_write(0x06000000,bytes([0xa5])*64)
   for reg,value in [(UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,0x06000000+odd),(UC_ARM_REG_R2,count),(UC_ARM_REG_SP,0x03007b00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
   u.emu_start(0x03005920,0x03007000,count=2000)
   assert u.reg_read(UC_ARM_REG_PC)==0x03007000
   expected=bytearray([0xa5]*64);expected[odd:odd+count]=bytes([index])*count
   assert bytes(u.mem_read(0x06000000,64))==expected,(index,odd,count)
   cases+=1
report=dict(result='PASS',original_arm_cases=cases,zero_cases=34,scope='Original model span03005920 writes index0 as opaque framebuffer index, preserves adjacent bytes for odd/even starts and lengths; palette color/timing not recovered.')
(p/'model-zero-index-tests.json').write_text(json.dumps(report,indent=2));print(report)
