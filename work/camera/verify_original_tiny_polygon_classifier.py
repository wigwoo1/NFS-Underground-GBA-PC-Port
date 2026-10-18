"""Replay the original ARM rectangle classifier on actual tiny-car polygons."""
import sys,json,struct,hashlib
from pathlib import Path
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR
from scene_batches import batches
file=Path(sys.argv[1]);report=json.loads(file.read_text());trace=Path(report['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==report['trace_sha256']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM);cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x02000000,0x40000);cpu.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);checks=[]
for batch in batches(trace):
 if not 12346<=batch['begin_refresh']<=12355:continue
 object_address=None
 for event in batch['events']:
  if event['pc']==0x03002628:object_address=event['blocks'][62][0]
  if event['pc']!=0x03003d4c or object_address!=0x020044fc:continue
  blocks=event['blocks'];polygon=bytearray(blocks[87][1]);struct.pack_into('<I',polygon,0,0x02000000);struct.pack_into('<I',polygon,8,0x02001000)
  cpu.mem_write(0x02000000,blocks[89][1]);cpu.mem_write(0x02001000,blocks[88][1]);cpu.mem_write(0x02002000,bytes(polygon));cpu.mem_write(0x02003000,blocks[86][1])
  cpu.reg_write(UC_ARM_REG_R0,0x02003000);cpu.reg_write(UC_ARM_REG_R1,0x02002000);cpu.reg_write(UC_ARM_REG_SP,0x03007c00);cpu.reg_write(UC_ARM_REG_LR,0x03006000)
  cpu.emu_start(0x03005824,0x030058c8,count=1000);actual=cpu.reg_read(UC_ARM_REG_R0);expected=event['regs'][0];assert actual==expected
  rectangle=list(struct.unpack('<4i',blocks[86][1]));count=struct.unpack_from('<I',polygon,20)[0];indices=struct.unpack('<'+'H'*count,blocks[88][1]);points=[struct.unpack_from('<2h',blocks[89][1],i*4) for i in indices]
  checks.append(dict(interval=[batch['begin_refresh'],batch['end_refresh']],original_result=expected,exact_arm_result=True,rectangle=rectangle,polygon_bbox=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]))
assert len(checks)==143
out=file.with_name(file.stem.replace('-verification','-tiny-classifier')+'.json');out.write_text(json.dumps(dict(result='PASS',cases=checks,scope='Exact original ARM5824..58C8 replay of captured tiny model polygon rectangle classifications. Flags only; later polygon clipping, scanline generation and texture write coverage remain separate.'),indent=2));print(json.dumps(dict(report=str(out),cases=len(checks),flags={str(v):sum(c['original_result']==v for c in checks) for v in sorted(set(c['original_result'] for c in checks))},rectangles=sorted(set(tuple(c['rectangle']) for c in checks)))))
