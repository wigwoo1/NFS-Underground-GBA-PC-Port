from pathlib import Path
import ctypes as C,struct,json,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();code=(p/'motion-original-model-spans-iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x1000000)]:u.mem_map(a,n)
u.mem_write(0x03000000,code);u.mem_write(0x08000000,rom);table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_edge_plan;f.argtypes=[C.c_void_p]*4+[C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
rng=random.Random(0x3980)
for case in range(2000):
 y=rng.randrange(-1000,1000);dy=rng.randrange(1,2000);a=[rng.randrange(-32768,32768),y];b=[rng.randrange(-32768,32768),y+dy];ua=[rng.randrange(65536) for _ in range(2)];ub=[rng.randrange(65536) for _ in range(2)];shift=rng.randrange(11);height=rng.randrange(1,1025);out=(C.c_uint32*7)();assert f((C.c_int16*2)(*a),(C.c_int16*2)(*b),(C.c_uint16*2)(*ua),(C.c_uint16*2)(*ub),shift,height,table,out)
 context=bytearray(48);struct.pack_into('<I',context,12,0x02001000);struct.pack_into('<2H',context,36,shift,height);poly=bytearray(32);struct.pack_into('<4I',poly,0,0x02002000,0x02003000,0x02004000,0x02005000);struct.pack_into('<I',poly,20,2)
 for address,data in [(0x02000000,bytes(context)),(0x02001000,bytes(poly)),(0x02002000,struct.pack('<4h',*a,*b)),(0x02003000,struct.pack('<4H',*ua,*ub)),(0x02004000,struct.pack('<2H',0,1)),(0x02005000,struct.pack('<2H',0,1))]:u.mem_write(address,data)
 for off,value in [(0x3a14,2),(0x3a18,0)]:u.mem_write(struct.unpack_from('<I',code,off)[0],struct.pack('<I',value))
 for reg,v in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,v)
 u.emu_start(0x03003980,0x03007000,count=1000);assert u.reg_read(UC_ARM_REG_R0)==1
 expected=[struct.unpack('<I',bytes(u.mem_read(struct.unpack_from('<I',code,off)[0],4)))[0] for off in [0x3b2c,0x3b20,0x3b30,0x3b38,0x3b34,0x3b3c,0x3b40]]
 assert list(out)==expected,(case,list(out),expected)
r=dict(result='PASS_NATIVE_MODEL_ASCENDING_EDGE_PLAN',original_ARM_cases=2000,accumulator_words=14000,scope='Ascending source edge arithmetic, unsigned source UV scaling, fixed16 X and Q8 UV slopes exact original backward edge walker on two-vertex rings. Full ring traversal/clip/row lifecycle unverified.')
(p/'model-edge-plan-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r)
