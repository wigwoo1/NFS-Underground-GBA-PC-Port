from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=d.nfs_visibility_object_sources;fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,65536),(0x03000000,65536),(0x04000000,65536)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());observed=[]
def hook(cpu,pc,n,ctx):
 if pc==0x03002000:observed.append(cpu.reg_read(UC_ARM_REG_R1));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
r=random.Random(5480);rejections=0;calls=0
for trial in range(128):
 state=bytearray(256);struct.pack_into('<I',state,12,0x02008000);struct.pack_into('<I',state,20,0x02001000);record=bytes(16);descs=bytearray(512*48);heads=bytearray(b'\xff'*1024);chain=r.sample(range(1,512),r.randrange(0,16))
 if trial%2:
  descs[18]=8;struct.pack_into('<H',descs,36,chain[0] if chain else 65535)
  for i,node in enumerate(chain):struct.pack_into('<H',descs,node*48+36,chain[i+1] if i+1<len(chain) else 65535)
  regions=chain
 else:regions=[0]
 for node in regions:struct.pack_into('<H',heads,node*2,65535 if r.randrange(3)==0 else r.randrange(256))
 u.mem_write(0x02000000,bytes(state));u.mem_write(0x02001000,bytes(descs));u.mem_write(0x02008000,bytes(heads));u.mem_write(0x02009000,record);observed.clear()
 for reg,val in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02009000),(UC_ARM_REG_SP,0x04008000)):u.reg_write(reg,val)
 u.emu_start(0x030054a0,0x03005564,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03005564
 out=C.create_string_buffer(4096);count=C.c_uint();assert fn(bytes(state),record,read,None,out,512,C.byref(count));native=[struct.unpack_from('<2I',out.raw,i*8)[1] for i in range(count.value)];assert native==observed;calls+=count.value
 if count.value:
  out=C.create_string_buffer(b'X'*4096,4096);count_bad=C.c_uint(123);assert not fn(bytes(state),record,read,None,out,count.value-1,C.byref(count_bad)) and out.raw==b'X'*4096 and count_bad.value==123;rejections+=1
report=dict(result='PASS',original_ARM_cases=128,source_heads=calls,atomic_capacity_rejections=rejections,scope='Own-region and sibling-chain source-head ordering against original54A0; object callbacks stubbed and enclosing eligibility supplied.')
(p/'object-source-tests.json').write_text(json.dumps(report,indent=2));print(report)
