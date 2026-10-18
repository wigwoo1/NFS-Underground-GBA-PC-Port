from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x40000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
def hook(uc,pc,size,ctx):
 if pc in [0x030021f8,0x03002204]:uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_object_insert;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
rng=random.Random(0x20f8);cases=0
for trial in range(32):
 objects=bytearray(rng.randbytes(32*164));head=C.c_uint32(65535);maximum=C.c_uint32(0x80000000)
 for i in range(32):struct.pack_into('<H',objects,i*164,i);struct.pack_into('<I',objects,i*164+0x28,rng.randrange(-8,9)&0xffffffff)
 buf=C.create_string_buffer(bytes(objects))
 for candidate in rng.sample(range(32),32):
  before=buf.raw[:32*164];distance=struct.unpack_from('<I',before,candidate*164+0x28)[0]
  u.mem_write(0x0200003c,struct.pack('<I',0x02001000));u.mem_write(0x02001000,before);u.mem_write(0x030070a4,struct.pack('<I',maximum.value));u.mem_write(0x030070e0,struct.pack('<I',head.value))
  for reg,val in [(UC_ARM_REG_R4,distance),(UC_ARM_REG_R6,0x02001000+candidate*164),(UC_ARM_REG_R7,0x02000000),(UC_ARM_REG_R8,65535)]:u.reg_write(reg,val)
  u.emu_start(0x030020f8,0x030021f8,count=10000)
  assert fn(buf,32,candidate,C.byref(head),C.byref(maximum))==1
  assert buf.raw[:32*164]==bytes(u.mem_read(0x02001000,32*164)) and head.value==struct.unpack('<I',u.mem_read(0x030070e0,4))[0] and maximum.value==struct.unpack('<I',u.mem_read(0x030070a4,4))[0],(trial,candidate)
  cases+=1
 # Duplicate candidate rejects atomically.
 before=buf.raw;h=head.value;m=maximum.value
 assert not fn(buf,32,candidate,C.byref(head),C.byref(maximum)) and buf.raw==before and head.value==h and maximum.value==m
report=dict(result='PASS',original_ARM_insertions=cases,duplicate_rejections=32,scope='Sorted object insertion, signed/equal distances,head/tail and full-buffer parity; no traversal/callback implementation.')
(root/'visibility-object-insert-tests.json').write_text(json.dumps(report,indent=2));print(report)
