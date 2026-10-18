"""Bounded original recursive draw diagnostic; raster leaves bypassed."""
from pathlib import Path
import json,struct,sys,os
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent/'pydeps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
raw=(p/os.environ.get('NF_ORACLE_FIXTURE','arm-oracle-fresh-16-17-50-after.bin')).read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000),(0x05000000,0x10000),(0x06000000,0x20000),(0x07000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x02000000,raw[:0x40000]);u.mem_write(0x03000000,raw[0x40000:]);u.mem_write(0x08000000,rom);events=[];regions=[];last_pc=0;active_road=None;region_stack=[]
regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7]
def hook(uc,pc,size,ctx):
 global last_pc,active_road
 last_pc=pc
 while region_stack and pc==region_stack[-1]['return_pc']:region_stack.pop()
 if active_road is not None and pc==active_road['return_pc']:
  active_road=None
 if active_road is not None and pc in (0x03003190,0x030056d8):
  params=struct.unpack('<16I',bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0),64)));active_road.setdefault('spans',[]).append([params[6],params[7],pc,struct.unpack('<I',bytes(uc.mem_read(0x03007098,4)))[0]])
 if pc==0x030027f0:
  address=uc.reg_read(UC_ARM_REG_R1);region=dict(record=bytes(uc.mem_read(address,16)).hex(),pass_value=uc.reg_read(UC_ARM_REG_R2),return_pc=uc.reg_read(UC_ARM_REG_LR));regions.append(region);region_stack.append(region)
 if pc in (0x03000304,0x030032f0):
  values=[uc.reg_read(r) for r in regs];state=bytes(uc.mem_read(values[1],256));events.append(dict(pc=hex(pc),registers=values,record=region_stack[-1]['record'],pass_value=region_stack[-1]['pass_value'],material=values[0],material_bytes=bytes(uc.mem_read(values[0],48)).hex(),bounds=struct.unpack_from('<4H',state,226)))
  if pc==0x03000304:
   events[-1]['wall_descriptor']=bytes(uc.mem_read(values[3],48)).hex();events[-1]['wall_flags']=values[2]
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  else:
   active_road=events[-1];active_road['return_pc']=uc.reg_read(UC_ARM_REG_LR);active_road['write_min']=None;active_road['write_max']=None
def write_hook(uc,access,address,size,value,ctx):
 if active_road is not None and 0x06000000<=address<0x06018000:
  lo=active_road['write_min'];hi=active_road['write_max'];active_road['write_min']=address if lo is None else min(lo,address);active_road['write_max']=address+size if hi is None else max(hi,address+size)
u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write_hook)
for reg,val in [(UC_ARM_REG_R0,0x030000c0),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03008000)]:u.reg_write(reg,val)
error=None
try:u.emu_start(0x03004d5c,0x03008000,count=2000000)
except Exception as e:error=str(e)
report=dict(result='DIAGNOSTIC_RETURN' if u.reg_read(UC_ARM_REG_PC)==0x03008000 else 'DIAGNOSTIC_INCOMPLETE',last_pc=hex(last_pc),error=error,regions=regions,events=events,scope='Copied RAM and ROM; dummy palette/IO/video; original road raster executes with writes recorded; wall raster bypass. Not fidelity proof or runnable native game.')
(p/'original-road-write-diagnostic.json').write_text(json.dumps(report,indent=2));print(report['result'],report['last_pc'],error,'regions',len(regions),'surfaces',len(events))








