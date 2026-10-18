"""Original first-pass draws for both sampled region87 occurrences."""
from pathlib import Path
import json,struct,sys
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');f=p/'visibility-overflow-171-wide';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();ew=(f/'ewram.bin').read_bytes();iw=(f/'iwram.bin').read_bytes();meta=json.loads((f/'sample-0.5.json').read_text());address=meta['state_address'];result=(f/'result-0.5.bin').read_bytes();pose=(f/'pose-0.5.bin').read_bytes();batch=(p/'overflow-scene-171/queue-plans.bin').read_bytes();m=json.loads((p/'overflow-scene-171/manifest.json').read_text());cases=[]
indices=[i for i in range(22) if struct.unpack_from('<H',result,256+i*16)[0]==87 and not struct.unpack_from('<H',result,266+i*16)[0]&8];assert indices==[0,10]
for qi in reversed(indices):
 record=result[256+qi*16:272+qi*16];u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for base,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000),(0x05000000,0x1000),(0x06000000,0x20000),(0x08000000,0x800000)):u.mem_map(base,size)
 u.mem_write(0x02000000,ew);u.mem_write(0x03000000,iw);u.mem_write(0x08000000,rom);u.mem_write(address,result[:256]);u.mem_write(struct.unpack_from('<I',result,84)[0],pose[56:104]);u.mem_write(0x04001000,record)
 calls=[];draws=[];objects=[]
 def hook(cpu,pc,length,ctx):
  if pc==0x030027f0:calls.append(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16)))
  if pc in (0x03000304,0x030032f0):
   draws.append((2 if pc==0x03000304 else 1,cpu.reg_read(UC_ARM_REG_R6 if pc==0x03000304 else UC_ARM_REG_R7)))
   cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
  if pc==0x0300220c:objects.append(pc);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 for reg,value in ((UC_ARM_REG_R0,address),(UC_ARM_REG_R1,0x04001000),(UC_ARM_REG_R2,0),(UC_ARM_REG_SP,0x0400ff00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,value)
 u.emu_start(0x030027f0,0x03006000,count=2000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03006000 and calls==[record] and not objects
 off=4+qi*2068;n=struct.unpack_from('<I',batch,off)[0]
 expected=[struct.unpack_from('<2I',batch,off+20+j*32) for j in range(n)]
 assert all(phase==0 for source,phase in expected)
 assert [source for kind,source in draws if kind==2]==[source for source,phase in expected]
 descriptor=struct.unpack_from('<I',result,20)[0]+87*48
 assert draws==[(2,source) for source,phase in expected]+[(1,descriptor)]
 cases.append(dict(queue_index=qi,record=list(struct.unpack('<8H',record)),draws=draws,wall_assets_exact=True,road_source=descriptor))
assert cases[0]['draws']==cases[1]['draws'] and cases[0]['record']!=cases[1]['record']
report=dict(result='PASS',cases=cases,scope='Original first-pass direct draw order for repeated87 matches native queue wall plans and one primary road. Independent routine invocations; raster leaves skipped. Second-pass object/model deduplication and full-scene composition unverified.')
(p/'repeated-region-trace-tests.json').write_text(json.dumps(report,indent=2));print(report)
