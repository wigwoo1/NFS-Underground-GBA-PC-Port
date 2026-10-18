from pathlib import Path
import ctypes as C,struct,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);fn=d.nfs_visibility_region_object_gate;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p];u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,65536),(0x03000000,65536),(0x04000000,65536)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());collections=[]
def hook(cpu,pc,n,ctx):
 if pc in (0x030054a0,0x0300220c):
  if pc==0x030054a0:collections.append(pc)
  cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
@Read
def reader(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
reciprocal=C.create_string_buffer(bytes(131072));accepted=0
for trial in range(128):
 state=bytearray(256);desc=bytearray(48);material=bytearray(20);record=struct.pack('<8H',0,0,240,0,158,trial,0,65535)
 for offset,value in ((16,0x0200c000),(20,0x02001000),(28,0x0200b000),(80,0x02009000),(120,0x0200d000 if trial&1 else 0)):struct.pack_into('<I',state,offset,value)
 struct.pack_into('<H',desc,10,0 if trial&2 else 65535);desc[18]=8 if trial&4 else 0;struct.pack_into('<H',material,8,64 if trial&8 else 0)
 u.mem_write(0x02000000,bytes(state));u.mem_write(0x02001000,bytes(desc));u.mem_write(0x02002000,record);u.mem_write(0x02009000,struct.pack('<2I',0,0x0200a000));u.mem_write(0x0200b000,bytes(material));collections.clear()
 for reg,v in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02002000),(UC_ARM_REG_R2,1),(UC_ARM_REG_SP,0x04008000),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,v)
 u.emu_start(0x030027f0,0x03006000,count=5000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 status=fn(bytes(state),record,1,reader,None,reciprocal);assert status==len(collections);accepted+=status
report=dict(result='PASS',original_ARM_cases=128,second_pass_collections=accepted,scope='Second-pass material hidden/callback-table gates versus original27F0; downstream collection/draw routines stubbed. First-pass geometry covered by full sampled oracle.')
(p/'region-object-gate-tests.json').write_text(json.dumps(report,indent=2));print(report)
