from pathlib import Path
import sys,ctypes as C,random,struct,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x3000000,0x10000);u.mem_map(0x2000000,0x40000)
code=rom[0x71b0c+0xd48:0x71b0c+0xefc];assert code[:4]==bytes.fromhex('f0472de9');u.mem_write(0x3000d48,code)
d=C.CDLL(str(Path('work/camera/native_camera.dll').resolve()));d.nfs_camera_transform.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
r=random.Random(1034);passed=0;culled=0
for case in range(1000):
 n=r.randrange(1,17);camera=bytearray(r.randbytes(48));src=bytearray(r.randbytes(68*n));offsets=r.randbytes(32*16);original=r.randbytes(52*n)
 for pos in [0,8,24,32]:struct.pack_into('<i',camera,pos,r.randint(-16384,16384))
 for pos in [36,40,44]:struct.pack_into('<i',camera,pos,r.randint(-10000,10000))
 for i in range(n):
  struct.pack_into('<ii',src,i*68,r.randint(-40000,40000),r.randint(-40000,40000));struct.pack_into('<H',src,i*68+42,r.choice([65535,r.randrange(16)]))
 state=bytearray(256);struct.pack_into('<I',state,0x54,0x2001000);struct.pack_into('<I',state,0x68,0x2020000);struct.pack_into('<I',state,0x18,0x2010000)
 for addr,data in [(0x2000000,state),(0x2001000,camera),(0x2002000,src),(0x2010000,offsets),(0x2020000,original)]:u.mem_write(addr,bytes(data))
 for reg,value in [(UC_ARM_REG_R0,0x2000000),(UC_ARM_REG_R1,0),(UC_ARM_REG_R2,0x2002000),(UC_ARM_REG_R3,n),(UC_ARM_REG_SP,0x3007f00),(UC_ARM_REG_LR,0x3007000)]:u.reg_write(reg,value)
 u.emu_start(0x3000d48,0x3007000,count=20000)
 dst=C.create_string_buffer(original);cb=C.create_string_buffer(bytes(camera));sb=C.create_string_buffer(bytes(src));ob=C.create_string_buffer(offsets)
 result=d.nfs_camera_transform(cb,sb,ob,dst,n)
 assert result==u.reg_read(UC_ARM_REG_R0),(case,'return')
 assert dst.raw[:n*52]==bytes(u.mem_read(0x2020000,n*52)),(case,'memory')
 passed+=1;culled+=not result
report={'result':'PASS','differential_cases':passed,'far_cull_cases':culled,'runtime_address':'03000D48','scope':'Native integer road camera transform compared with original ARM code; not integrated into host and not a smooth camera solution.'};Path('work/camera/native-camera-tests.json').write_text(json.dumps(report,indent=2));print(report)
