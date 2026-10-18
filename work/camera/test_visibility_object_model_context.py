from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@READ
def read(ctx,address,out,size):
 try:C.memmove(out,bytes(u.mem_read(address,size)),size);return 1
 except:return 0
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_model_context;fn.argtypes=[C.c_void_p]*4+[READ,C.c_void_p,C.c_void_p]
def hook(uc,pc,size,ctx):
 if pc in (0x03002628,0x0300262c):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook);rng=random.Random(2588);ready=0;hidden=0
for case in range(512):
 state=bytearray(rng.randbytes(256));struct.pack_into('<I',state,0x7c,0x02001000);obj=bytearray(rng.randbytes(164));index=case%16+1;struct.pack_into('<h',obj,0x36,index);obj[0x88]=255 if case%7==0 else case%32
 material=rng.randbytes(32);context=rng.randbytes(68);depth=[0,511,512,1024][case%4];params=(C.c_uint32*4)(depth,rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32))
 for address,data in [(0x02000000,bytes(state)),(0x02000300,bytes(obj)),(0x02000400,material),(0x02001000,rng.randbytes(18*40)),(0x02018048,context),(0x02018000,struct.pack('<II',params[1],params[2])),(0x02018018,struct.pack('<I',params[3]))]:u.mem_write(address,data)
 for reg,val in [(UC_ARM_REG_R6,0x02000000),(UC_ARM_REG_R7,0x02000300),(UC_ARM_REG_R4,0x02000400),(UC_ARM_REG_IP,depth),(UC_ARM_REG_R9,index),(UC_ARM_REG_SP,0x02018000)]:u.reg_write(reg,val)
 u.emu_start(0x03002588,0x03002630,count=100)
 out=C.create_string_buffer(context);result=fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(bytes(obj)),C.create_string_buffer(material),params,read,None,out)
 assert result==int(obj[0x88]!=255) and out.raw[:68]==bytes(u.mem_read(0x02018048,68)),case
 ready+=result;hidden+=1-result
report=dict(result='PASS',original_ARM_context_cases=512,ready=ready,hidden=hidden,scope='Model context construction only; model rasterization remains external.')
(root/'visibility-object-model-context-tests.json').write_text(json.dumps(report,indent=2));print(report)
