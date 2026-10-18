from pathlib import Path
import ctypes as C,struct,json,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();code=(p/'motion-original-model-spans-iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x1000000)]:u.mem_map(a,n)
u.mem_write(0x03000000,code);u.mem_write(0x08000000,rom);table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_row_plan;f.argtypes=[C.c_uint32]*7+[C.c_void_p]*2;captured=[]
def hook(cpu,address,size,data):
 if address==0x03005920:
  globals=[struct.unpack('<I',bytes(cpu.mem_read(struct.unpack_from('<I',code,0x5a34+i*4)[0],4)))[0] for i in range(4)]
  captured.extend([cpu.reg_read(UC_ARM_REG_R1),cpu.reg_read(UC_ARM_REG_R2),*globals]);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook);rng=random.Random(0x3ec8);visible=0
for case in range(2000):
 x=rng.randrange(-100,240);left=((x<<16)+rng.randrange(65536))&0xffffffff;right=(((x+rng.randrange(-2,120))<<16)+rng.randrange(65536))&0xffffffff;uv=[rng.getrandbits(32) for _ in range(4)];base=0x06000000;out=(C.c_uint32*6)();assert f(left,right,*uv,base,table,out)
 stack=bytearray(64);struct.pack_into('<I',stack,4,base);struct.pack_into('<I',stack,44,uv[2]);struct.pack_into('<I',stack,36,uv[3]);u.mem_write(0x03007d00,bytes(stack));u.mem_write(0x02001028,struct.pack('<I',0x02020000))
 for reg,v in [(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_R6,right),(UC_ARM_REG_R7,left),(UC_ARM_REG_R10,uv[0]),(UC_ARM_REG_R8,uv[1]),(UC_ARM_REG_R9,0x02001000)]:u.reg_write(reg,v)
 captured.clear();u.emu_start(0x03003ec8,0x03003f38,count=100);assert (captured==list(out)) if captured else out[1]==0
 visible+=bool(captured)
r=dict(result='PASS_NATIVE_MODEL_ROW_PLAN',original_ARM_cases=2000,visible_rows=visible,scope='Row width/destination and wrapped Q8 U/V increments exact original row block. Edge walking and clipped polygon-to-row generation remain unverified.')
(p/'model-row-plan-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r)
