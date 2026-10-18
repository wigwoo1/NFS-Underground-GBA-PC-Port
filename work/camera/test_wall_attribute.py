from pathlib import Path
import ctypes,random,struct,sys,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM);cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x02000000,0x40000)
cpu.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
native=ctypes.CDLL(str(Path('work/camera/native_wall.dll').resolve()));native.nfs_wall_restore_attribute.argtypes=[ctypes.c_uint32,ctypes.c_uint32];native.nfs_wall_restore_attribute.restype=ctypes.c_uint32
r=random.Random(0x810)
for case in range(2000):
 a=r.getrandbits(32);b=r.getrandbits(32);reciprocal=struct.unpack_from('<I',rom,0x627700+4*r.randrange(1,0x6000))[0]
 cpu.mem_write(0x03007e38,struct.pack('<3I',b,a,0))
 for reg,value in [(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,reciprocal),(UC_ARM_REG_R8,0x02001000),(UC_ARM_REG_R9,0)]:cpu.reg_write(reg,value)
 cpu.emu_start(0x03000810,0x03000858,count=40)
 assert cpu.reg_read(UC_ARM_REG_R1)==native.nfs_wall_restore_attribute(a,reciprocal)
 assert cpu.reg_read(UC_ARM_REG_R12)==native.nfs_wall_restore_attribute(b,reciprocal)
report={'result':'PASS','randomized_original_ARM_cases':2000,'attribute_comparisons':4000,'scope':'Perspective attribute restoration block, including 32-bit overflow and signed shifts. Complete shade accumulator/interpolation and live renderer integration remain unfinished.'}
Path('work/camera/wall-attribute-tests.json').write_text(json.dumps(report,indent=2));print(report)
