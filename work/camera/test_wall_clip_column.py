from pathlib import Path
import ctypes as C,random,struct,sys,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
d=C.CDLL(str((root/'native_wall.dll').resolve()));fn=d.nfs_wall_clip_column
fn.argtypes=[C.c_uint32]*6+[C.c_void_p]
r=random.Random(0xafc);clipped=visible=0
for case in range(3000):
 top=r.randrange(-250*16384,250*16384);bottom=top+r.randrange(-4*16384,400*16384)
 clip_top=r.randrange(0,80);clip_bottom=r.randrange(clip_top,161);step=r.getrandbits(32);v=r.getrandbits(32)
 u.mem_write(0x020000e6,struct.pack('<2H',clip_top,clip_bottom))
 u.mem_write(0x03007e00,struct.pack('<2I',(bottom>>14)&0xffffffff,top&0xffffffff))
 u.mem_write(0x03007e3c,struct.pack('<I',0x02000000))
 for reg,value in [(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_R7,top),(UC_ARM_REG_R8,bottom),(UC_ARM_REG_R10,top>>14),(UC_ARM_REG_R4,(bottom>>14)-(top>>14)+1),(UC_ARM_REG_R5,v),(UC_ARM_REG_R12,step)]:u.reg_write(reg,value&0xffffffff)
 u.emu_start(0x03000afc,0x03000b38,count=100)
 expected=[struct.unpack('<I',u.mem_read(0x03007e04,4))[0],u.reg_read(UC_ARM_REG_R4),u.reg_read(UC_ARM_REG_R5)]
 actual=(C.c_uint32*3)();assert fn(top,bottom,clip_top,clip_bottom,step,v,actual)
 assert list(actual)==expected,(case,list(actual),expected)
 clipped+=top<(clip_top<<14) or bottom>=(clip_bottom<<14)
 visible+=C.c_int32(actual[1]).value>0
out=(C.c_uint32*3)();assert fn(10<<14,20<<14,0,160,123,0,out) and list(out)==[10<<14,12,0]
report=dict(result='PASS',original_ARM_cases=3000,clipped_cases=clipped,positive_count_cases=visible,
 extra_terminal_row_verified=True,scope='Original fixed-point vertical clip/count/texture-offset component only; not integrated into continuous world-space rendering.')
(root/'wall-clip-column-tests.json').write_text(json.dumps(report,indent=2));print(report)
