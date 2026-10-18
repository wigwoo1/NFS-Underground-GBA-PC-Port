"""Original ARM top-level queue dispatch versus C on fresh sampled builds."""
from pathlib import Path
import ctypes as C,json,struct,sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent/'pydeps'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nfs_visibility_draw_plan.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x10000);calls=[]
def hook(uc,pc,size,ctx):
 if pc==0x030027f0:
  calls.append(((uc.reg_read(UC_ARM_REG_R1)-queue_address)//16,uc.reg_read(UC_ARM_REG_R2)));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook);checks=[]
for path in sorted(p.glob('arm-oracle-fresh-*-after.bin')):
 raw=path.read_bytes();state=raw[0x400c0:0x401c0];queue_address=struct.unpack_from('<I',state,96)[0];count=struct.unpack_from('<H',state,238)[0];off=queue_address-0x02000000 if queue_address<0x03000000 else 0x40000+queue_address-0x03000000;queue=raw[off:off+512]
 u.mem_write(0x02000000,raw[:0x40000]);u.mem_write(0x03000000,raw[0x40000:]);calls.clear()
 for reg,val in [(UC_ARM_REG_R0,0x030000c0),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03008000)]:u.reg_write(reg,val)
 u.emu_start(0x03004d5c,0x03008000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03008000
 out=(C.c_uint32*128)();n=C.c_uint();assert d.nfs_visibility_draw_plan(C.create_string_buffer(queue,512),count,out,64,C.byref(n));native=[tuple(out[i*2:i*2+2]) for i in range(n.value)];assert native==calls,(path.name,native,calls)
 checks.append(dict(file=path.name,queue_count=count,calls=native,exact=True))
assert len(checks)==202
report=dict(result='PASS_TOP_LEVEL_DISPATCH',checks=checks,scope='Original ARM03004d5c queue traversal and scratch clear; region leaf030027f0 bypassed and calls recorded. Proves top-level queue index/pass order only, not recursive leaf draw occurrences/material/clipping/60fps.')
(p/'sampled-original-dispatch-audit.json').write_text(json.dumps(report,indent=2));print('PASS',len(checks),'dispatch cases')
