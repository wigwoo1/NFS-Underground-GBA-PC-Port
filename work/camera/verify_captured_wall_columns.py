"""Independently execute captured source-scene ARM terminal wall writers."""
from pathlib import Path
import sys,json,struct,ctypes as C
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
p=Path('work/camera');out=Path('outputs/nfsug-native-renderer/camera-research')
capture=json.loads((out/'original-wall-column-audit.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x800000)):u.mem_map(address,size)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
d=C.CDLL(str((p/'native_wall.dll').resolve()));d.nfs_wall_unshaded_addresses.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
reads=[];writes=[]
def on_read(cpu,access,address,size,value,ctx):
 if 0x08000000<=address<0x08800000:
  assert size==1;reads.append(address)
def on_write(cpu,access,address,size,value,ctx):
 assert size==1;writes.append((address,value))
u.hook_add(UC_HOOK_MEM_READ,on_read)
u.hook_add(UC_HOOK_MEM_WRITE,on_write,begin=0x06000000,end=0x0601ffff)
rows=opaque=zero=0;results=[]
for c in capture['selected_columns']:
 state=struct.pack('<17I',*c['state']);src=(C.c_uint*320)();dst=(C.c_uint*320)();buffer=C.create_string_buffer(state)
 assert d.nfs_wall_unshaded_addresses(buffer,int(c['destination'],16),c['starting_v'],c['rows'],src,dst)
 assert list(src)[:c['rows']]==c['source_addresses']
 expected=[]
 for i in range(c['rows']):
  value=rom[src[i]-0x08000000]
  if value:expected.append((dst[i],value));opaque+=1
  else:zero+=1
 u.mem_write(0x03007a00,state);reads.clear();writes.clear()
 for reg,value in ((UC_ARM_REG_R0,0x03007a00),(UC_ARM_REG_R1,int(c['destination'],16)),(UC_ARM_REG_R2,c['starting_v']),(UC_ARM_REG_R3,c['rows']),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03007000)):u.reg_write(reg,value)
 u.emu_start(0x030053e8,0x03007000,count=1000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03007000
 assert reads==c['source_addresses'] and writes==expected
 rows+=c['rows'];results.append(dict(texture=c['texture'],rows=c['rows'],writes=len(writes),skipped_zero=c['rows']-len(writes)))
report=dict(result='PASS',captured_columns=len(results),exact_source_reads=rows,exact_nonzero_writes=opaque,exact_zero_skips=zero,columns=results,scope='Original ARM terminal routine independently matches native address plan and zero-skip writes for captured source-scene columns through page flip. Not GPU sampling or whole-scene verification.')
(out/'captured-wall-column-arm-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='columns'}))
