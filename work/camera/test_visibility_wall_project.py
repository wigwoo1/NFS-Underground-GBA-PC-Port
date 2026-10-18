from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for addr,size in [(0x03000000,0x10000),(0x02000000,0x10000),(0x08000000,len(rom))]:u.mem_map(addr,size)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);u.mem_write(0x08000000,rom)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_wall_project
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
rng=random.Random(0x1cb4);rejected=visible=flipped=0
for case in range(1600):
 initial=bytearray(rng.randbytes(52));struct.pack_into('<2h',initial,4,rng.randrange(1,32768),rng.randrange(1,32768))
 flags=rng.getrandbits(16)&~6
 if case&1:flags|=2
 if case&2:flags|=0x2000
 struct.pack_into('<H',initial,0x30,flags)
 values=[rng.choice([128,256,512,1024,0xffffffff]),120,80,0,240]
 if case%4==0:values=[rng.getrandbits(32) for _ in range(5)]
 params=(C.c_uint32*5)(*values)
 u.mem_write(0x02000000,bytes(initial));sp=0x02001000
 for off,val in [(0x4c,values[0]),(0x54,values[1]),(0x50,values[2]),(0x48,values[3]),(0x44,values[4]),(0x40,0)]:u.mem_write(sp+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R5,0x02000000),(UC_ARM_REG_R6,flags),(UC_ARM_REG_SP,sp)]:u.reg_write(reg,val)
 u.emu_start(0x03001cb4,0x03001fa8,count=300);assert u.reg_read(UC_ARM_REG_PC)==0x03001fa8
 out=C.create_string_buffer(bytes(initial));assert fn(out,params,recip)==1
 assert out.raw[:52]==bytes(u.mem_read(0x02000000,52)),case
 finalflags=struct.unpack_from('<H',out.raw,0x30)[0]
 rejected+=bool(finalflags&4);visible+=not bool(finalflags&4);flipped+=bool(finalflags&2)
for depth in [0,-1,-32768]:
 initial=bytearray(52);struct.pack_into('<2h',initial,4,depth,64);out=C.create_string_buffer(bytes(initial))
 assert fn(out,params,recip)==0 and out.raw[:52]==initial
report=dict(result='PASS',original_ARM_synthetic_cases=1600,visible=visible,rejected=rejected,flipped=flipped,invalid_depth_checks=3,scope='Wall projection, orientation and horizontal rejection; original surface vertex emission disabled. No full-scene gameplay claim.')
(root/'visibility-wall-project-tests.json').write_text(json.dumps(report,indent=2));print(report)
