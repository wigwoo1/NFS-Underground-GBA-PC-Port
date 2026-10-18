"""Execute captured original arrow-wall spans independently; diagnostic only."""
from pathlib import Path
import sys,struct,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from scene_batches import batches
from PIL import Image
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x800000)]:u.mem_map(address,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
written=set()
def writes(cpu,access,address,size,value,data):
 written.update(range(address-0x06000000,address-0x06000000+size))
u.hook_add(UC_HOOK_MEM_WRITE,writes,begin=0x06000000,end=0x06013fff)
active=None;calls=0
for e in next(batches(root/'shading-spans.bin'))['events']:
 if e['pc']==0x03000304:active=e['blocks'][5][0]
 if active!=0x857c6f4 or e['pc']!=0x030053e8:continue
 address,data=e['blocks'][75];u.mem_write(address,data)
 for index in range(13):u.reg_write(UC_ARM_REG_R0+index,e['regs'][index])
 u.reg_write(UC_ARM_REG_SP,0x03007e00);u.reg_write(UC_ARM_REG_LR,0x03007000)
 u.emu_start(e['pc'],0x03007000,count=1000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03007000
 calls+=1
assert calls==11
pixels=bytes(u.mem_read(0x06000000,240*160));reference=(root/'reference-scene-0-page.bin').read_bytes()
valid=sorted(i for i in written if 0<=i<240*160)
mismatches=sum(pixels[i]!=reference[i] for i in valid)
pal=struct.unpack('<256H',(root/'reference-scene-0-palette.bin').read_bytes())
colors=[tuple(((v>>shift)&31)*255//31 for shift in (0,5,10)) for v in pal]
rgb=bytes(c for i,p in enumerate(pixels) for c in (colors[p] if i in written else (32,32,32)))
Image.frombytes('RGB',(240,160),rgb).resize((960,640),Image.Resampling.NEAREST).save(root/'original-arrow-span-replay.png')
report=dict(original_calls=calls,written_pixels=len(valid),different_from_reference_page=mismatches,
 scope='Original ARM column execution from captured registers/state. A mismatch may indicate later overdraw or reference alignment, not a native-renderer defect by itself.')
(root/'arrow-span-replay.json').write_text(json.dumps(report,indent=2));print(report)
