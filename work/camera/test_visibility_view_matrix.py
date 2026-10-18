from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_view_matrix
fn.argtypes=[C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p]
table=C.create_string_buffer(rom[0x623700:0x627700]);rng=random.Random(0x6dd04)
for angle in range(16384):
 position=[rng.getrandbits(32) for _ in range(3)]
 for reg,val in [(UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,angle),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x0806dd05,0x03006000,count=1000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 sp=0x03007d00
 for off,val in [(0x98,0x02001000),(0xa8,position[0]),(0xac,position[2])]:u.mem_write(sp+off,struct.pack('<I',val))
 u.mem_write(0x03006738,bytes(4));u.reg_write(UC_ARM_REG_R5,position[1])
 u.emu_start(0x08002ead,0x08002ec6,count=100)
 assert u.reg_read(UC_ARM_REG_PC)==0x08002ec6
 out=(C.c_uint32*12)();assert fn(angle,(C.c_uint32*3)(*position),table,out)
 assert bytes(out)==bytes(u.mem_read(0x02001000,48)),angle
captured=0
for name in json.loads((root/'pipeline-capture-manifest.json').read_text()):
 blob=(root/'pipeline-corpus'/name).read_bytes();stride=88+0x48000
 h=struct.unpack_from('<22I',blob);ram=blob[2*stride+88:3*stride]
 def mem(addr,n):
  off=addr-0x02000000 if addr<0x03000000 else 0x40000+addr-0x03000000
  return ram[off:off+n]
 def word(addr):return struct.unpack('<I',mem(addr,4))[0]
 sp=h[19];bob=word(0x03006738);bob=bob-(1<<32) if bob&0x80000000 else bob
 position=[word(sp+0xa8),(word(sp+0xb0)+16+(bob>>8))&0xffffffff,word(sp+0xac)]
 out=(C.c_uint32*12)();assert fn(word(0x03006730),(C.c_uint32*3)(*position),table,out)
 assert bytes(out)==mem(word(h[4]+0x54),48),name
 captured+=1
report=dict(result='PASS',original_Thumb_angle_cases=16384,full_width_translation_cases=16384,actual_builder_matrices_exact=captured,
 scope='Fixed14 yaw construction and negative-position translation. Captured final yaw/position inputs are used; interstage camera-position and angle policy remain to be recovered.')
(root/'visibility-view-matrix-tests.json').write_text(json.dumps(report,indent=2));print(report)
