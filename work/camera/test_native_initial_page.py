from pathlib import Path
import sys,ctypes as C,struct,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
p=Path('work/camera');u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x03000000,0x10000),(0x06000000,0x20000),(0x08000000,0x1000000)]:u.mem_map(a,n)
u.mem_write(0x03000000,(p/'motion-original-initial-inputs-iwram.bin').read_bytes())
d=C.CDLL(str((p/'native_initial_page.dll').resolve()))
d.nfs_initial_fill.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32]
d.nfs_initial_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t]+[C.c_uint32]*4
checks=[]
for e in records(p/'motion-original-initial-inputs-world.bin'):
 if e['pc']!=0xffff0095:continue
 pc,_,_=struct.unpack('<3I',e['blocks'][95][1]);r=e['regs'];initial=bytes((i*37+13)&255 for i in range(0x20000));native=C.create_string_buffer(initial,len(initial));u.mem_write(0x06000000,initial)
 for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR],r):u.reg_write(reg,value)
 u.reg_write(UC_ARM_REG_LR,0x03006000)
 if pc==0x03003814:
  sp=r[13];u.mem_write(sp,e['blocks'][96][1]);a,src=e['blocks'][97];u.mem_write(a,src);ss,ds=struct.unpack('<2I',e['blocks'][96][1])
  assert d.nfs_initial_copy(native,len(initial),r[0]-0x06000000,src,len(src),r[2],r[3],ss,ds)
 else:assert d.nfs_initial_fill(native,len(initial),r[0]-0x06000000,r[1],r[2])
 u.emu_start(pc,0x03006000,count=200000)
 actual=bytes(u.mem_read(0x06000000,len(initial)));assert native.raw==actual,(e['frame'],hex(pc))
 checks.append(dict(refresh=e['frame'],pc=hex(pc),compared_bytes=len(initial)))
report=dict(result='PASS_NATIVE_INITIAL_PRODUCER_BUFFERS',cases=len(checks),comparison_bytes=sum(c['compared_bytes'] for c in checks),checks=checks,scope='Captured original fill/copy inputs versus original ARM entire buffer. Does not prove retained initial page state or 4K/live timing.')
(p/'native-initial-producer-buffer-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report['result'],report['cases'],report['comparison_bytes'])

