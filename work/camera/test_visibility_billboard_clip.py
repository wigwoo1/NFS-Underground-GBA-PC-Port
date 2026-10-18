from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import *
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x647700]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_map(0x08000000,0x800000);u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
f=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_billboard_clip;f.argtypes=[C.c_void_p]*5;rng=random.Random(0x4ea8);recip=C.create_string_buffer(table);counts={}
def stop(uc,address,size,user):
 if address in (0x03005058,0x030050ec):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,stop)
for case in range(1600):
 x=rng.randrange(-300,400);y=rng.randrange(-200,300);w=rng.randrange(0,500);h=rng.randrange(0,400)
 rect=(C.c_uint32*4)(x,x+w,y,y+h);uv=(C.c_uint32*4)(rng.randrange(16),rng.randrange(16),rng.randrange(512),rng.randrange(512));bounds=(C.c_uint16*4)(0,240,0,160)
 state=bytearray(256);struct.pack_into('<4H',state,0xe2,0,240,0,160);u.mem_write(0x02000400,bytes(state));context=bytearray(48);struct.pack_into('<I',context,12,0x02000800);context[16:32]=bytes(uv);u.mem_write(0x02000600,bytes(context));u.mem_write(0x02000800,struct.pack('<4I',rect[0],rect[2],rect[1],rect[3]))
 for reg,val in [(UC_ARM_REG_R0,0x02000600),(UC_ARM_REG_R1,0x02000400),(UC_ARM_REG_SP,0x02018000)]:u.reg_write(reg,val)
 u.emu_start(0x03004ea8,0x030050f0,count=200)
 out=(C.c_uint32*8)(*([0xabcdef01]*8));before=bytes(out);result=f(rect,uv,bounds,recip,out)
 pc=u.reg_read(UC_ARM_REG_PC)
 if pc==0x03005058:
  sp=u.reg_read(UC_ARM_REG_SP);read=lambda off:struct.unpack('<I',u.mem_read(sp+off,4))[0]
  expected=[u.reg_read(r) for r in [UC_ARM_REG_R6,UC_ARM_REG_LR,UC_ARM_REG_R4,UC_ARM_REG_R7]]+[read(12),u.reg_read(UC_ARM_REG_R5),u.reg_read(UC_ARM_REG_R8),read(8)]
  assert result==1 and list(out)==expected,(case,result,list(out),expected)
 else:
  original=C.c_int32(u.reg_read(UC_ARM_REG_R0)).value;assert pc==0x030050ec and result==original and bytes(out)==before,(case,hex(pc),result,original)
 counts[str(result)]=counts.get(str(result),0)+1
report=dict(result='PASS',original_ARM_clip_cases=1600,outcomes=counts,scope='Positive bounded rectangle setup only; no rasterization or live alternate-path coverage.')
(root/'visibility-billboard-clip-tests.json').write_text(json.dumps(report,indent=2));print(report)
