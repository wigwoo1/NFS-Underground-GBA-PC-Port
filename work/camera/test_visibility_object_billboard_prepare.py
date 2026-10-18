from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import *
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x647700]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_map(0x08000000,0x800000);u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
f=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_billboard_prepare;f.argtypes=[C.c_void_p]*7;rng=random.Random(24605058);recip=C.create_string_buffer(table);counts={};captured={}
def stop(uc,address,size,user):
 if address==0x03002578:
  sp=0x02018000;b=bytes(uc.mem_read(sp+0x28,16));l,t,r,bt=struct.unpack('<4I',b)
  ctx=bytes(uc.mem_read(sp+0x48,44));width,height=struct.unpack_from('<II',ctx,24);stride,mh=struct.unpack_from('<HH',ctx,36);texture=struct.unpack_from('<I',ctx,40)[0]
  captured['head']=[l,r,t,bt,width,height,texture,stride,mh]
 if address in (0x03005058,0x030050ec):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,stop)
for case in range(1024):
 obj=bytearray(164);size=rng.randrange(64,1024);struct.pack_into('<h',obj,0x70,size);m=bytearray(rng.randbytes(64))
 for off in (0,32):
  struct.pack_into('<HH',m,off+8,rng.randrange(8,128),rng.randrange(8,128));struct.pack_into('<HH',m,off+0x16,0,0)
 p=(C.c_uint32*9)(rng.randrange(-1000,1000),rng.randrange(-1000,1000),rng.choice([128,512,2048,4096,6000]),256,120,80,rng.randrange(2),0x02009000,0x0200a000)
 bounds=(C.c_uint16*4)(0,240,0,160);state=bytearray(256);struct.pack_into('<I',state,4,p[7]);struct.pack_into('<4H',state,0xe2,*bounds);u.mem_write(0x02000400,bytes(m));u.mem_write(0x02000800,bytes(state))
 for off,val in [(0,0x02000c00),(4,p[8]),(8,p[2]),(12,p[1]),(16,p[0]),(24,p[3]),(28,p[5]),(32,p[4])]:u.mem_write(0x02018000+off,struct.pack('<I',val))
 for reg,val in [(UC_ARM_REG_R0,size),(UC_ARM_REG_R4,0x02000400),(UC_ARM_REG_R5,0x08627700),(UC_ARM_REG_R6,0x02000800),(UC_ARM_REG_R9,p[6]),(UC_ARM_REG_SP,0x02018000)]:u.reg_write(reg,val)
 u.emu_start(0x03002460,0x030050f0,count=300)
 out=(C.c_uint32*18)(*([0xabcdef01]*18));before=bytes(out);result=f(C.create_string_buffer(bytes(obj)),C.create_string_buffer(bytes(m[:32])),C.create_string_buffer(bytes(m[32:])),p,bounds,recip,out)
 pc=u.reg_read(UC_ARM_REG_PC)
 if pc==0x03005058:
  sp=u.reg_read(UC_ARM_REG_SP);read=lambda off:struct.unpack('<I',u.mem_read(sp+off,4))[0]
  clip=[u.reg_read(r) for r in [UC_ARM_REG_R6,UC_ARM_REG_LR,UC_ARM_REG_R4,UC_ARM_REG_R7]]+[read(12),u.reg_read(UC_ARM_REG_R5),u.reg_read(UC_ARM_REG_R8),read(8)]
  assert result==1 and list(out[:9])==captured['head'] and list(out[10:])==clip,(case,result,list(out),captured,clip)
 else:
  original=C.c_int32(u.reg_read(UC_ARM_REG_R0)).value;assert pc==0x030050ec and result==original and bytes(out)==before,(case,hex(pc),result,original)
 counts[str(result)]=counts.get(str(result),0)+1
report=dict(result='PASS',original_ARM_composed_cases=1024,outcomes=counts,scope='2460 through clipping setup including actual context construction; no pixel loop or live route coverage.')
(root/'visibility-object-billboard-prepare-tests.json').write_text(json.dumps(report,indent=2));print(report)
