from pathlib import Path
import ctypes as C,random,struct,sys,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x800000)]:u.mem_map(address,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
r=random.Random(0xadc);texture=bytes(0 if i%3==0 else r.randrange(1,256) for i in range(0x20000));u.mem_write(0x02010000,texture)
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint8))
@Reader
def read(context,address,out):
 if not 0x02010000<=address<0x02010000+len(texture):return 0
 out[0]=texture[address-0x02010000];return 1
d=C.CDLL(str((root/'native_wall.dll').resolve()));fn=d.nfs_wall_default_column
fn.argtypes=[C.c_void_p]+[C.c_uint32]*7+[C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);writes=[]
def wrote(cpu,access,address,size,value,data):
 assert size==1;writes.append((address,value))
u.hook_add(UC_HOOK_MEM_WRITE,wrote,begin=0x06000000,end=0x0601ffff)
total=empty=0
for case in range(500):
 top=r.randrange(-30*16384,150*16384);bottom=top+r.randrange(1,90*16384)
 clip_top=r.randrange(0,30);clip_bottom=r.randrange(100,160);raw_v=r.randrange(0,8192);span=r.randrange(1,32768)
 shift=r.randrange(2,9);height=1<<r.randrange(2,9);state=bytearray(68)
 for offset,value in {8:120,12:shift,16:height,24:case%2,28:(1<<shift)*height,36:0x02010000,52:r.getrandbits(32),64:((1<<shift)<<15)-1}.items():struct.pack_into('<I',state,offset,value)
 u.mem_write(0x03007900,bytes(state));u.mem_write(0x020000e6,struct.pack('<2H',clip_top,clip_bottom))
 u.mem_write(0x02001018,struct.pack('<2I',raw_v,span))
 for offset,value in {0:(bottom>>14)&0xffffffff,4:top&0xffffffff,8:0x06000020,0x38:0x02001000,0x3c:0x02000000}.items():u.mem_write(0x03007e00+offset,struct.pack('<I',value))
 for reg,value in [(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_R4,(bottom>>14)-(top>>14)+1),(UC_ARM_REG_R6,0x03007900),(UC_ARM_REG_R7,top),(UC_ARM_REG_R8,bottom),(UC_ARM_REG_R10,top>>14)]:u.reg_write(reg,value&0xffffffff)
 writes.clear();u.emu_start(0x03000adc,0x03000b60,count=1000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03000b60
 addresses=(C.c_uint32*320)();values=(C.c_uint8*320)();count=C.c_uint(999)
 assert fn(C.create_string_buffer(bytes(state)),0x06000020,top,bottom,clip_top,clip_bottom,span,raw_v<<8,table,read,None,addresses,values,C.byref(count))
 actual=list(zip(list(addresses)[:count.value],list(values)[:count.value]));assert actual==writes,(case,actual[:5],writes[:5])
 total+=count.value;empty+=count.value==0
# A source-memory failure must not publish a partial write list.
@Reader
def fail(context,address,out):return 0
count.value=123;addresses[0]=0xdeadbeef;values[0]=77
assert not fn(C.create_string_buffer(bytes(state)),0x06000020,0,10<<14,0,160,8192,0,table,fail,None,addresses,values,C.byref(count))
assert (count.value,addresses[0],values[0])==(123,0xdeadbeef,77)
report=dict(result='PASS',composed_original_ARM_cases=500,matched_nonzero_writes=total,empty_columns=empty,
 failure_preserves_outputs=True,scope='Default column step, viewport clipping, texture addressing, LOD and transparent writes composed in native code. Does not recover horizontal wall dispatch or full-scene rendering.')
(root/'default-column-tests.json').write_text(json.dumps(report,indent=2));print(report)

