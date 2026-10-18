"""Validate retained wall V fields and default span setup against original ARM code."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x02000000,0x40000);cpu.mem_map(0x08000000,0x800000)
cpu.mem_write(0x08000000,rom);cpu.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
fields=0;defaults=0;extended=0;nonunit=0;skipped=0
for event in records(root/'world.bin'):
 if event['pc']!=0x03000304:continue
 b=event['blocks'];source=b[5][1];edge=b[6][1];anim=b[70][1];height=u(b[8][1],38)
 for source_offset,edge_offset,flag in [(16,24,8),(24,28,8),(20,32,16),(28,36,16)]:
  if u(edge,48)&flag:skipped+=1;continue
  expected=(i(source,source_offset)+(h(anim,6)>>1))&0xffffffff
  assert i(edge,edge_offset)&0xffffffff==expected,(event['id'],source_offset)
  fields+=1
 if event['regs'][2]&128:extended+=1;continue
 defaults+=1
 start=i(edge,24)/(128*height);span=i(edge,28)/(128*height)
 nonunit+=start!=0 or span!=1
 cpu.mem_write(0x02001000,edge)
 cpu.mem_write(0x03007e50,struct.pack('<I',0x02001000))
 length=1+event['id']%159
 for reg,value in [(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_R7,length)]:cpu.reg_write(reg,value)
 cpu.emu_start(0x03000898,0x030008b0,count=100)
 assert cpu.reg_read(UC_ARM_REG_R10)==(i(edge,24)<<8)&0xffffffff
 lut=struct.unpack_from('<I',rom,0x627700+length*4)[0]
 assert cpu.reg_read(UC_ARM_REG_R0)==((i(edge,28)*lut)>>16)&0xffffffff
 # The flag-0x100 path has separate setup code with the same contract.
 cpu.mem_write(0x03007e38,struct.pack('<I',0x02001000));cpu.reg_write(UC_ARM_REG_R4,length)
 cpu.emu_start(0x03000adc,0x03000af8,count=100)
 assert cpu.reg_read(UC_ARM_REG_R5)==(i(edge,24)<<8)&0xffffffff
 assert cpu.reg_read(UC_ARM_REG_R0)==((i(edge,28)*lut)>>16)&0xffffffff
assert fields and defaults
report=dict(result='PASS',uncut_vertical_fields=fields,clipped_fields_skipped=skipped,default_setup_ARM_comparisons=defaults,extended_mode_draws=extended,default_draws_with_nonunit_V=nonunit,scope='Source-to-edge fields and default vertical start/span setup; not full rasterizer, shading, or extended-mode projection validation.')
(root/'wall-vertical-tests.json').write_text(json.dumps(report,indent=2));print(report)
