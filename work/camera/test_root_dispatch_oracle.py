"""Native root schedule versus original ARM dispatcher, including flag80."""
from pathlib import Path
import ctypes as C,json,struct,sys,random
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for base,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000)):u.mem_map(base,size)
u.mem_write(0x03000000,rom[0x71b0c:0x77b0c]);calls=[]
def hook(cpu,pc,length,ctx):
 pointer=cpu.reg_read(UC_ARM_REG_R1);calls.append((int((pointer-0x04001000)//16),cpu.reg_read(UC_ARM_REG_R2),*struct.unpack('<4I',cpu.mem_read(pointer,16))));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook,begin=0x030027f0,end=0x030027f0)
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_root_region_schedule;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
r=random.Random(0x4d5c);checked=skipped80=0
for case in range(132):
 count=case%33;raw=b''.join(struct.pack('<8H',i,0,238,0,158,r.choice((0,1,8,0x80,0x81,0x88)),i%6,0) for i in range(count))
 u.mem_write(0x02000060,struct.pack('<I',0x04001000));u.mem_write(0x020000ee,struct.pack('<H',count));u.mem_write(0x04001000,raw)
 calls.clear();u.reg_write(UC_ARM_REG_R0,0x02000000);u.reg_write(UC_ARM_REG_SP,0x0400ff00);u.reg_write(UC_ARM_REG_LR,0x03006000)
 u.emu_start(0x03004d5c,0x03006000,count=100000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 output=C.create_string_buffer(4+32*48);assert fn(raw,count,output)
 n=struct.unpack_from('<I',output.raw)[0];assert [struct.unpack_from('<6I',output.raw,4+i*24) for i in range(n)]==calls,case
 skipped80+=sum(bool(struct.unpack_from('<H',raw,i*16+10)[0]&0x80) and not struct.unpack_from('<H',raw,i*16+10)[0]&8 for i in range(count));checked+=1
report=dict(result='PASS',original_ARM_cases=checked,flag80_second_pass_exclusions=skipped80,scope='Original root dispatcher with root draw routines stubbed. Exact occurrence order/pass/record parity; no nested eligibility proof.')
(p/'root-dispatch-oracle-tests.json').write_text(json.dumps(report,indent=2));print(report)
