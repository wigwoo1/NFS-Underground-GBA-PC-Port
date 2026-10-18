from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);table=rom[0x627700:0x62f700];u.mem_write(0x02001000,table);u.mem_write(0x03002584,struct.pack('<I',0x02001000))
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_visible;fn.argtypes=[C.c_void_p,C.c_void_p];recip=C.create_string_buffer(table)
def hook(uc,pc,size,ctx):
 if pc in (0x030023b8,0x0300262c):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook);rng=random.Random(2368);visible=0;culled=0
for case in range(2048):
 z=([0,1,8191,8192,0xffffffff][case%5] if case<100 else rng.randrange(1,9000));y=rng.randrange(-2000,2001)&0xffffffff;scale=256;cy=80;top=0;bottom=160
 if case>=1024:y=rng.getrandbits(32);scale=rng.getrandbits(32);cy=rng.getrandbits(32);top=rng.randrange(65536);bottom=rng.randrange(65536)
 p=(C.c_uint32*6)(y,z,scale,cy,top,bottom)
 for off,val in [(12,y),(24,scale),(28,cy)]:u.mem_write(0x02018000+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_SP,0x02018000),(UC_ARM_REG_IP,z),(UC_ARM_REG_R8,top),(UC_ARM_REG_R10,bottom)]:u.reg_write(reg,val)
 u.emu_start(0x03002368,0x03002630,count=100)
 result=fn(p,recip);assert result==int(u.reg_read(UC_ARM_REG_PC)==0x030023b8),(case,list(p),result)
 visible+=result;culled+=1-result
report=dict(result='PASS',original_ARM_visibility_cases=2048,visible=visible,culled=culled,scope='Non-region depth and vertical visibility gate only; material and draw dispatch remain external.')
(root/'visibility-object-visible-tests.json').write_text(json.dumps(report,indent=2));print(report)
