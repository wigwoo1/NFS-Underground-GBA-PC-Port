"""Recover palette-index shading lookup using the original wall pixel loop."""
from pathlib import Path
import hashlib,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
root=Path('work/camera');tables={};draws=0
for event in records(root/'shading.bin'):
 if event['pc']!=0x03000304:continue
 address,data=event['blocks'][74];assert len(data)==4096
 tables[hashlib.sha256(data).hexdigest()]=(address,data);draws+=1
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM);cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x02000000,0x40000)
cpu.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);checked=0
for address,data in tables.values():
 cpu.mem_write(0x02002000,data)
 for texel in range(256):
  for shade in range(16):
   cpu.mem_write(0x02001000,bytes([texel]));cpu.mem_write(0x02000000,b'\xad')
   for reg,value in [(UC_ARM_REG_R0,0),(UC_ARM_REG_R9,0x7fff),(UC_ARM_REG_R10,15),(UC_ARM_REG_R6,0),(UC_ARM_REG_R4,0x02001000),(UC_ARM_REG_R7,0x02002000+shade),(UC_ARM_REG_R1,0x02000000)]:cpu.reg_write(reg,value)
   cpu.emu_start(0x030053b0,0x030053cc,count=16)
   actual=cpu.mem_read(0x02000000,1)[0]
   assert actual==(data[texel*16+shade] if texel else 0xad),(texel,shade)
   checked+=1
assert draws and checked
report={'result':'PASS','captured_wall_draws':draws,'unique_tables':len(tables),'original_pixel_loop_comparisons':checked,'tables':[{'address':hex(address),'sha256':digest,'texels_with_shade_variation':sum(len(set(data[t*16:t*16+16]))>1 for t in range(1,256))} for digest,(address,data) in tables.items()], 'scope':'Captured palette remapping and transparent index zero validated. Shade-level selection by distance/material and LOD remain unresolved; no renderer lighting change yet.'}
(root/'wall-shading-tests.json').write_text(json.dumps(report,indent=2));print(report)
