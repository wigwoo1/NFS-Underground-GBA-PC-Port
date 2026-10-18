from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_object_branch_prepare;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,65536),(0x03000000,65536),(0x04000000,65536)):u.mem_map(a,n)
u.mem_write(0x03000000,(p/'visibility-overflow-171-wide/iwram.bin').read_bytes());r=random.Random(2284);selected=0
for trial in range(500):
 original=r.randbytes(256);obj=bytearray(r.randbytes(164));struct.pack_into('<H',obj,54,r.randrange(512));parent=r.randbytes(16);matrix=r.randbytes(48);state=C.create_string_buffer(original,256);record=C.create_string_buffer(b'X'*16,16);xyz=(C.c_uint32*3)();branch=C.c_uint()
 assert fn(state,bytes(obj),parent,matrix,xyz,C.byref(branch),record)==1;selected+=branch.value
 for a,b in ((0x02001000,original),(0x02002000,parent),(0x02003000,bytes(obj)),(0x02005000,matrix),(0x04008000,bytes(256)),(0x04008024,struct.pack('<I',0x02002000)),(0x04008014,struct.pack('<I',0x02005000))):u.mem_write(a,b)
 for reg,v in ((UC_ARM_REG_R6,0x02001000),(UC_ARM_REG_R7,0x02003000),(UC_ARM_REG_SP,0x04008000),(UC_ARM_REG_R5,0)):u.reg_write(reg,v)
 stop=0x03002360 if branch.value else 0x03002368;u.emu_start(0x03002284,stop,count=100)
 assert u.reg_read(UC_ARM_REG_PC)==stop and bytes(u.mem_read(0x02001000,256))==state.raw
 assert list(xyz)==[struct.unpack('<I',bytes(u.mem_read(0x04008000+o,4)))[0] for o in (16,12,8)]
 if branch.value:assert bytes(u.mem_read(0x04008048,16))==record.raw
 else:assert record.raw==b'X'*16
bad=bytearray(164);struct.pack_into('<H',bad,10,16);struct.pack_into('<H',bad,54,512);state=C.create_string_buffer(b'Z'*256,256);record=C.create_string_buffer(b'X'*16,16);xyz=(C.c_uint32*3)(1,2,3);branch=C.c_uint(123)
assert fn(state,bytes(bad),bytes(16),bytes(48),xyz,C.byref(branch),record)==-1 and state.raw==b'Z'*256 and record.raw==b'X'*16 and list(xyz)==[1,2,3] and branch.value==123
report=dict(result='PASS',original_ARM_cases=500,recursive_branches=selected,atomic_invalid_region=True,scope='Original2284 through2360/2368 full state, wrapped XYZ and recursive record; drawing not executed.')
(p/'object-branch-prepare-tests.json').write_text(json.dumps(report,indent=2));print(report)
