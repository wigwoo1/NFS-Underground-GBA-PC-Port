from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
class Cursor(C.Structure):_fields_=[('current',C.c_uint32),('count',C.c_uint32),('seen',C.c_uint8*512)]
d=C.CDLL(str((root/'native_visibility.dll').resolve()));begin=d.nfs_visibility_object_cursor_begin;advance=d.nfs_visibility_object_cursor_advance
begin.argtypes=[C.POINTER(Cursor),C.c_uint,C.c_uint];advance.argtypes=[C.POINTER(Cursor),C.c_void_p]
observed=[];rewrite=False

def hook(uc,pc,size,ctx):
 if pc==0x03002020:observed.append(uc.reg_read(UC_ARM_REG_R1))
 if pc==0x030021f8 and rewrite:uc.mem_write(uc.reg_read(UC_ARM_REG_R6)+2,struct.pack('<H',65535))
 if pc==0x03002204:uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
rng=random.Random(2027);cases=0;nodes=0
for count in range(0,257,4):
 for rewrite in (False,True):
  order=list(range(count));rng.shuffle(order);objects=bytearray(count*164)
  for i,index in enumerate(order):struct.pack_into('<HH',objects,index*164,index,order[i+1] if i+1<count else 65535)
  u.mem_write(0x0200003c,struct.pack('<I',0x02001000));u.mem_write(0x030070c0,bytes(32))
  if objects:u.mem_write(0x02001000,bytes(objects))
  head=order[0] if order else 65535;observed.clear()
  for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,head),(UC_ARM_REG_SP,0x03007c00)]:u.reg_write(reg,val)
  u.emu_start(0x03002000,0x03002208,count=20000)
  cursor=Cursor();result=begin(C.byref(cursor),head,count);native=[]
  while result==1:
   index=cursor.current;native.append(index);obj=bytearray(objects[index*164:(index+1)*164])
   if rewrite:struct.pack_into('<H',obj,2,65535)
   result=advance(C.byref(cursor),C.create_string_buffer(bytes(obj)))
  assert result==0 and native==observed,(count,rewrite,native,observed)
  assert advance(C.byref(cursor),None)==0
  cases+=1;nodes+=len(native)
cursor=Cursor();assert begin(C.byref(cursor),0,2)==1
obj=bytearray(164)
for next_index in (0,2):
 struct.pack_into('<H',obj,2,next_index);before=bytes(cursor)
 assert advance(C.byref(cursor),C.create_string_buffer(bytes(obj)))==-1 and bytes(cursor)==before
struct.pack_into('<H',obj,2,1);assert advance(C.byref(cursor),C.create_string_buffer(bytes(obj)))==1
struct.pack_into('<H',obj,2,0);before=bytes(cursor)
assert advance(C.byref(cursor),C.create_string_buffer(bytes(obj)))==-1 and bytes(cursor)==before
assert begin(C.byref(cursor),2,2)==-1 and bytes(cursor)==before
report=dict(result='PASS',original_ARM_traversals=cases,observed_nodes=nodes,post_processing_link_rewrite_cases=65,atomic_invalid_cases=4,scope='Source +02 traversal with inactive objects; synthetic post-processing link rewrite. Callback execution and sorting composition remain external.')
(root/'visibility-object-cursor-tests.json').write_text(json.dumps(report,indent=2));print(report)
