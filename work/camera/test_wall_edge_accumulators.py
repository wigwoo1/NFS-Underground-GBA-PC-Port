from pathlib import Path
import ctypes,struct,random,json,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
cpu.mem_map(0x03000000,0x10000);cpu.mem_map(0x08000000,0x1000000)
cpu.mem_write(0x03000000,Path('work/camera/motion-original-span-iwram.bin').read_bytes());cpu.mem_write(0x08000000,rom)
table=(ctypes.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
dll=ctypes.CDLL(str(Path('work/camera/native_wall.dll').resolve()))
f=dll.nfs_wall_edge_accumulators;f.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
def arm(pc,a,index):
 cpu.reg_write(UC_ARM_REG_R0,a&0xffffffff);cpu.reg_write(UC_ARM_REG_R1,index)
 cpu.reg_write(UC_ARM_REG_SP,0x03007f00);cpu.reg_write(UC_ARM_REG_LR,0x03007ffc)
 cpu.emu_start(pc,0x03007ffc,count=100)
 return cpu.reg_read(UC_ARM_REG_R0)
r=random.Random(0x478)
for case in range(2000):
 left=r.randrange(-150,100);width=r.randrange(2,150);right=left+width
 z=[r.randrange(64,32768) for _ in range(2)];ys=[r.randrange(-160,320) for _ in range(4)];uv=[r.getrandbits(32) for _ in range(2)];rev=case%2
 edge=bytearray(52);struct.pack_into('<8h',edge,0,left*2,right*2,z[0],z[1],*ys);struct.pack_into('<2I',edge,16,*uv);struct.pack_into('<H',edge,48,rev*2)
 buf=ctypes.create_string_buffer(bytes(edge));out=(ctypes.c_uint32*8)();assert f(buf,table,out)
 order=[rev,1-rev]
 start=[(table[z[order[0]]]<<8)&0xffffffff,arm(0x030052f8,uv[order[0]],z[order[0]]),(ys[order[0]]<<14)&0xffffffff,(ys[2+order[0]]<<14)&0xffffffff]
 end=[(table[z[order[1]]]<<8)&0xffffffff,arm(0x030052f8,uv[order[1]],z[order[1]]),(ys[order[1]]<<14)&0xffffffff,(ys[2+order[1]]<<14)&0xffffffff]
 expected=start+[arm(0x0300527c,b-a,width) for a,b in zip(start,end)]
 assert list(out)==expected,(case,list(out),expected)
report={'result':'PASS_WALL_EDGE_ACCUMULATORS','random_original_ARM_cases':2000,'verified_accumulator_words':16000,'scope':'Default prepared-edge endpoint association and fixed-point accumulator arithmetic. Full wall planner, clipping, column sequence, live GPU and full-scene timing remain unverified.'}
Path('work/camera/wall-edge-accumulator-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
