import sys,json,random
from pathlib import Path
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
from owned_sky_scroll import source_offset
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x08000000,0x80000);u.mem_write(0x08000000,rom[:0x80000]);u.mem_map(0x03000000,0x8000)
rng=random.Random(614);checks=0
cases=[(a,240,120) for a in (0,1,4095,4096,4097,8191,8192,12287,12288,16383,16384,0xffffffff)]+[(rng.getrandbits(32),rng.randint(1,65535),rng.randint(-32768,32767)) for _ in range(1000)]
for angle,width,center in cases:
 u.mem_write(0x03005abc,(center&65535).to_bytes(2,'little'));u.reg_write(UC_ARM_REG_R0,angle);u.reg_write(UC_ARM_REG_R9,width);u.reg_write(UC_ARM_REG_SP,0x03007c00)
 u.emu_start(0x08004bdd,0x08004bf8,count=10000)
 value=u.reg_read(UC_ARM_REG_R0);value=value-(1<<32) if value&(1<<31) else value
 assert (value&~1)==source_offset(angle,width,center),(angle,width,center,value)
 checks+=1
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-scroll-arithmetic-20261006');out.mkdir(parents=True,exist_ok=True)
(out/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Original Thumb horizontal phase/remainder/signed-center instructions versus recovered formula; even alignment separately recovered from08004c98..4c9a; no live sky integration'),indent=2))
for name in ('owned_sky_scroll.py','test_sky_scroll_original.py'):(out/name).write_text((Path('work/camera')/name).read_text())
print('PASS original sky scroll arithmetic',checks)
