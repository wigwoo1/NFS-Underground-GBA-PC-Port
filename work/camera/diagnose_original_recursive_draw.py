"""Bounded original recursive draw diagnostic; raster leaves bypassed."""
from pathlib import Path
import json,struct,sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent/'pydeps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
raw=(p/'arm-oracle-fresh-16-17-50-after.bin').read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000),(0x05000000,0x10000),(0x06000000,0x20000),(0x07000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x02000000,raw[:0x40000]);u.mem_write(0x03000000,raw[0x40000:]);u.mem_write(0x08000000,rom);events=[];regions=[];last_pc=0
regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7]
def hook(uc,pc,size,ctx):
 global last_pc
 last_pc=pc
 if pc==0x030027f0:
  address=uc.reg_read(UC_ARM_REG_R1);regions.append(dict(record=bytes(uc.mem_read(address,16)).hex(),pass_value=uc.reg_read(UC_ARM_REG_R2)))
 if pc in (0x03000304,0x030032f0):
  values=[uc.reg_read(r) for r in regs];state=bytes(uc.mem_read(values[1],256));events.append(dict(pc=hex(pc),registers=values,bounds=struct.unpack_from('<4H',state,226)))
  uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
for reg,val in [(UC_ARM_REG_R0,0x030000c0),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03008000)]:u.reg_write(reg,val)
error=None
try:u.emu_start(0x03004d5c,0x03008000,count=2000000)
except Exception as e:error=str(e)
report=dict(result='DIAGNOSTIC_RETURN' if u.reg_read(UC_ARM_REG_PC)==0x03008000 else 'DIAGNOSTIC_INCOMPLETE',last_pc=hex(last_pc),error=error,regions=regions,events=events,scope='Copied RAM and ROM; dummy palette/IO/video; road and wall raster entry bypass. Not fidelity proof or runnable native game.')
(p/'original-recursive-draw-diagnostic.json').write_text(json.dumps(report,indent=2));print(report['result'],report['last_pc'],error,'regions',len(regions),'surfaces',len(events))
