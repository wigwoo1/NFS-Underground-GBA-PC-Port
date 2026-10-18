from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_object_region_prepare;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,65536),(0x03000000,65536),(0x04000000,65536)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());r=random.Random(843);selected=0
for trial in range(500):
 state=r.randbytes(256);obj=bytearray(r.randbytes(164));struct.pack_into('<H',obj,54,r.randrange(512));parent=r.randbytes(16);native=C.create_string_buffer(state,256);record=C.create_string_buffer(b'X'*16,16);status=fn(native,bytes(obj),parent,record);selected+=status
 u.mem_write(0x02001000,state);u.mem_write(0x02002000,parent);u.mem_write(0x02003000,bytes(obj));u.mem_write(0x02005000,bytes(48));u.mem_write(0x04008000,bytes(256));u.mem_write(0x04008024,struct.pack('<I',0x02002000));u.mem_write(0x04008014,struct.pack('<I',0x02005000))
 for reg,v in ((UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_R6,0x02001000),(UC_ARM_REG_R7,0x02003000),(UC_ARM_REG_SP,0x04008000),(UC_ARM_REG_LR,struct.unpack_from('<H',obj,10)[0]),(UC_ARM_REG_R2,0),(UC_ARM_REG_R3,0),(UC_ARM_REG_R4,0)):u.reg_write(reg,v)
 stop=0x03002360 if status else 0x03002368;u.emu_start(0x030022d8,stop,count=100);assert u.reg_read(UC_ARM_REG_PC)==stop and bytes(u.mem_read(0x02001000,256))==native.raw
 if status:assert bytes(u.mem_read(0x04008048,16))==record.raw
 else:assert record.raw==b'X'*16
bad=bytearray(164);struct.pack_into('<H',bad,10,16);struct.pack_into('<H',bad,54,512);state=C.create_string_buffer(b'Z'*256,256);record=C.create_string_buffer(b'X'*16,16)
assert fn(state,bytes(bad),bytes(16),record)==-1 and state.raw==b'Z'*256 and record.raw==b'X'*16
report=dict(result='PASS',original_arm_cases=500,selected=selected,invalid_region_atomic=True,scope='Original22D8..2360/2368 viewport/state/record branch parity; selected objects supplied explicitly.')
(p/'object-region-prepare-tests.json').write_text(json.dumps(report,indent=2));print(report)
