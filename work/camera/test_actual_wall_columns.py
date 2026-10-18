from pathlib import Path
import sys,ctypes as C,struct,random,json
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from scene_batches import records
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x800000)]:u.mem_map(address,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,(root/'motion-original-span-iwram.bin').read_bytes())
r=random.Random(0x53e8);u.mem_write(0x02000000,bytes(0 if i%3==0 else r.randrange(1,256) for i in range(0x40000)))
d=C.CDLL(str((root/'native_wall.dll').resolve()));fn=d.nfs_wall_unshaded_addresses
fn.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p]
reads=[];writes=[]
def read(cpu,access,address,size,value,data):
 if 0x02000000<=address<0x02040000 or 0x08000000<=address<0x08800000:
  assert size==1;reads.append(address)
def write(cpu,access,address,size,value,data):
 assert size==1;writes.append((address,value))
u.hook_add(UC_HOOK_MEM_READ,read)
u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0x06000000,end=0x0601ffff)
rows=0;lod_cases=0
def check(state,destination,vertical,count):
 global rows,lod_cases
 src=(C.c_uint32*320)();dst=(C.c_uint32*320)();buffer=C.create_string_buffer(state)
 assert fn(buffer,destination,vertical,count,src,dst)
 expected=[]
 for i in range(count):
  index=u.mem_read(src[i],1)[0]
  if index:expected.append((dst[i],index))
 reads.clear();writes.clear();u.mem_write(0x03007a00,state)
 for reg,value in [(UC_ARM_REG_R0,0x03007a00),(UC_ARM_REG_R1,destination),(UC_ARM_REG_R2,vertical),(UC_ARM_REG_R3,count),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03007000)]:u.reg_write(reg,value)
 u.emu_start(0x030053e8,0x03007000,count=1000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03007000
 assert reads==list(src)[:count],('texture addresses',reads,list(src)[:count])
 assert writes==expected,('writes',writes,expected)
 rows+=count;lod_cases+=bool(struct.unpack_from('<I',state,24)[0] and struct.unpack_from('<I',state,44)[0]>0x1b000)
live=0;raw=(root/'motion-original-span-hooks.bin').read_bytes()
for offset in range(0,len(raw),140):
 words=struct.unpack_from('<35I',raw,offset)
 if words[1]!=0x030053e8:continue
 regs=words[2:18];state=struct.pack('<17I',*words[18:]);check(state,regs[1],regs[2],regs[3]);live+=1
report=dict(result='PASS_ACTUAL_WALL_COLUMN_READ_WRITES',captured_columns=live,texture_row_addresses=rows,reduced_lod_cases=lod_cases,scope='Native unshaded addressing and skip/nonzero writes vs original ARM for actual captured columnstates. Captured prepared state used as componentinput; no native world projection/columnstate or fullscene proof.')
(root/'actual-wall-column-tests.json').write_text(json.dumps(report,indent=2));print(report)
