"""Verify original scanline palette-zero writer and its bounded table walk."""
from pathlib import Path
import sys,struct,json,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');code=(p/'live-multimodel-baseline-iwram.bin').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for base,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x1000),(0x05000000,0x1000)]:u.mem_map(base,size)
u.mem_write(0x03000000,code)
pointer=struct.unpack_from('<I',code,0x204)[0];assert pointer==0x03005e18
rng=random.Random(0x1c0);cases=0
for trial in range(8):
 colors=[rng.randrange(65536) for _ in range(80)]
 u.mem_write(0x02001000,struct.pack('<80H',*colors))
 u.mem_write(pointer,struct.pack('<I',0x02001000))
 u.mem_write(0x05000000,struct.pack('<H',0x1234))
 for row in range(228):
  before_pointer=bytes(u.mem_read(pointer,4));before_palette=bytes(u.mem_read(0x05000000,2))
  status=rng.randrange(65536);u.mem_write(0x04000004,struct.pack('<2H',status,row))
  u.reg_write(UC_ARM_REG_LR,0x03007000);u.emu_start(0x030001c0,0x03007000,count=100)
  assert u.reg_read(UC_ARM_REG_PC)==0x03007000
  if row<80:
   assert bytes(u.mem_read(0x05000000,2))==struct.pack('<H',colors[row])
   assert bytes(u.mem_read(pointer,4))==struct.pack('<I',0x02001000+2*(row+1))
   # Original uses ADD, not OR: retain exact wraparound behavior.
   assert bytes(u.mem_read(0x04000004,2))==struct.pack('<H',(status+0x200)&65535)
  else:
   assert bytes(u.mem_read(pointer,4))==before_pointer and bytes(u.mem_read(0x05000000,2))==before_palette
   assert bytes(u.mem_read(0x04000004,2))==struct.pack('<H',status)
  cases+=1
report=dict(result='PASS',original_arm_cases=cases,table_colors_verified=640,inactive_rows_verified=1184,pointer_address=pointer,scope='Original ARM writer consumes80halfwords for VCOUNT0..79, advances owned pointer and adds0x200 to DISPSTAT; invocation timing relative to captured display rows remains unverified.')
(p/'scanline-palette-zero-tests.json').write_text(json.dumps(report,indent=2));print(report)
