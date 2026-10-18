from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM);cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x02000000,0x40000);cpu.mem_map(0x08000000,0x800000)
cpu.mem_write(0x08000000,rom);cpu.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
d=C.CDLL(str((root/'native_wall.dll').resolve()));d.nfs_wall_shade_column.argtypes=[C.c_void_p,C.c_int,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);r=random.Random(5320)
for case in range(1000):
 edge=bytearray(52);left=r.randrange(-30,30);width=r.randrange(3,120)
 struct.pack_into('<4h',edge,0,left*2,(left+width)*2,r.randrange(64,20000),r.randrange(64,20000))
 struct.pack_into('<4h',edge,8,10,12,100,110)
 struct.pack_into('<2h',edge,40,r.randrange(16)*256,r.randrange(16)*256);struct.pack_into('<H',edge,48,2*(case%2))
 material=bytearray(48);struct.pack_into('<2I',material,8,0x02003000,0x02002000);struct.pack_into('<2H',material,36,6,64)
 cpu.mem_write(0x02001000,bytes(material));cpu.mem_write(0x02002000,bytes(edge));cpu.mem_write(0x02003000,bytes(64));cpu.mem_write(0x02004000,bytes(32))
 for reg,value in [(UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,0x02005000),(UC_ARM_REG_R2,0),(UC_ARM_REG_R3,0x02004000),(UC_ARM_REG_SP,0x03007f00)]:cpu.reg_write(reg,value)
 cpu.emu_start(0x03000304,0x030005a0,count=1000)
 sp=cpu.reg_read(UC_ARM_REG_SP);step=r.randrange(width)
 def word(offset):return struct.unpack('<I',cpu.mem_read(sp+offset,4))[0]
 q=(cpu.reg_read(UC_ARM_REG_R5)+step*cpu.reg_read(UC_ARM_REG_R4))&0xffffffff
 a=(cpu.reg_read(UC_ARM_REG_R8)+step*word(32))&0xffffffff
 cpu.mem_write(sp+72,struct.pack('<I',q));cpu.mem_write(sp+56,struct.pack('<I',a));cpu.reg_write(UC_ARM_REG_R8,0x02006000)
 cpu.emu_start(0x03000800,0x03000858,count=100)
 actual=C.c_int16(cpu.reg_read(UC_ARM_REG_R12)>>16).value
 expected=d.nfs_wall_shade_column(C.create_string_buffer(bytes(edge)),left+step,table)
 assert expected==actual,(case,expected,actual)
report={'result':'PASS','random_original_ARM_shade_columns':1000,'coverage':'Varying endpoint intensities 0..15, depths 64..19999, reversed edges, negative starting columns. Original setup and restoration blocks executed.'}
(root/'wall-shade-random-tests.json').write_text(json.dumps(report,indent=2));print(report)
