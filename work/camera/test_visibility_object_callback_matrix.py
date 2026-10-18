from pathlib import Path
import ctypes as C,json,random,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000);u.mem_map(0x02000000,0x20000);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
class Cursor(C.Structure):_fields_=[('current',C.c_uint32),('count',C.c_uint32),('seen',C.c_uint8*512)]
class Collector(C.Structure):_fields_=[('cursor',Cursor),('awaiting_callback',C.c_uint)]
d=C.CDLL(str((root/'native_visibility.dll').resolve()));begin=d.nfs_visibility_object_cursor_begin;begin.argtypes=[C.POINTER(Cursor),C.c_uint,C.c_uint]
step=d.nfs_visibility_object_collect_step;step.argtypes=[C.POINTER(Collector),C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
class Delta(C.Structure):_fields_=[('offset',C.c_uint32),('before',C.c_uint32),('after',C.c_uint32)]
apply=d.nfs_visibility_object_callback_apply;apply.argtypes=[C.POINTER(Collector),C.c_void_p,C.c_uint,C.c_uint,C.POINTER(Delta),C.c_uint]
rejections=0
arm_calls=[]
def mutate(obj):
 index=struct.unpack_from('<H',obj)[0];struct.pack_into('<H',obj,8,4 if index%2 else 0)
 struct.pack_into('<i',obj,20,(index+1)*256)
 if index%7==0:struct.pack_into('<H',obj,2,65535)
def change_matrix(values,index):
 values[9]=(values[9]+index+1)&0xffffffff
 values[11]=(values[11]-2)&0xffffffff
 return values
def hook(uc,pc,size,ctx):
 if pc==0x0201f000:
  addr=uc.reg_read(UC_ARM_REG_R6);obj=bytearray(uc.mem_read(addr,164));arm_calls.append(struct.unpack_from('<H',obj)[0]);mutate(obj);uc.mem_write(addr,bytes(obj));uc.mem_write(0x02000800,struct.pack('<12I',*change_matrix(list(struct.unpack('<12I',uc.mem_read(0x02000800,48))),arm_calls[-1])));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 if pc==0x03002204:uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook);rng=random.Random(20002090);callbacks=0;steps=0
for trial in range(128):
 count=32;order=rng.sample(range(count),count);objects=bytearray(count*164);visited=bytearray(32)
 for j,i in enumerate(order):
  struct.pack_into('<HHH',objects,i*164,i,order[j+1] if j+1<count else 65535,65535)
  struct.pack_into('<H',objects,i*164+8,rng.choice([0,1,4,5,7]));struct.pack_into('<H',objects,i*164+0x48,int(i%5!=0))
  struct.pack_into('<i',objects,i*164+12,rng.randrange(-20,21)*256);struct.pack_into('<i',objects,i*164+20,rng.randrange(-20,21)*256)
  if i%9==0:visited[i//8]|=1<<(i%8)
 matrix=(C.c_uint32*12)(16384,0,0,0,16384,0,0,0,16384,0,0,0)
 u.mem_write(0x0200003c,struct.pack('<I',0x02001000));u.mem_write(0x02000054,struct.pack('<I',0x02000800));u.mem_write(0x02000800,bytes(matrix));u.mem_write(0x02000078,struct.pack('<I',0x0201e000));u.mem_write(0x0201e000,struct.pack('<I',0x0201f000));u.mem_write(0x02001000,bytes(objects));u.mem_write(0x030070c0,bytes(visited));u.mem_write(0x030070a4,struct.pack('<I',0x80000000));u.mem_write(0x030070e0,struct.pack('<I',65535));arm_calls.clear()
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,order[0]),(UC_ARM_REG_SP,0x03007c00)]:u.reg_write(reg,val)
 u.emu_start(0x03002000,0x03002208,count=30000)
 c=Collector();begin(C.byref(c.cursor),order[0],count);buf=C.create_string_buffer(bytes(objects));bits=C.create_string_buffer(bytes(visited));head=C.c_uint32(65535);maximum=C.c_uint32(0x80000000);selector=C.c_uint32();native_calls=[]
 for guard in range(100):
  result=step(C.byref(c),buf,bits,32,matrix,C.byref(head),C.byref(maximum),C.byref(selector))
  if result==0:break
  assert result in (1,2)
  if result==2:
   assert selector.value==0;index=c.cursor.current;native_calls.append(index);obj=bytearray(buf.raw[index*164:(index+1)*164]);old=bytes(obj);mutate(obj)
   records=[Delta(index*164+i,old[i],obj[i]) for i in range(164) if old[i]!=obj[i]];delta=(Delta*len(records))(*records)
   before=buf.raw
   assert not apply(C.byref(c),buf,index,1,delta,len(records)) and buf.raw==before
   assert not apply(C.byref(c),buf,(index+1)%count,0,delta,len(records)) and buf.raw==before
   rejections+=2
   if records:
    bad=(Delta*1)(Delta(records[0].offset,(records[0].before+1)%256,records[0].after))
    assert not apply(C.byref(c),buf,index,0,bad,1) and buf.raw==before
    duplicate=(Delta*2)(records[0],records[0])
    assert not apply(C.byref(c),buf,index,0,duplicate,2) and buf.raw==before
    rejections+=2
   assert apply(C.byref(c),buf,index,0,delta,len(records))==1
   values=change_matrix(list(matrix),index)
   for lane,value in enumerate(values):matrix[lane]=value
  steps+=1
 else:raise AssertionError('did not terminate')
 assert native_calls==arm_calls and buf.raw[:count*164]==bytes(u.mem_read(0x02001000,count*164)) and bits.raw[:32]==bytes(u.mem_read(0x030070c0,32))
 assert head.value==struct.unpack('<I',u.mem_read(0x030070e0,4))[0] and maximum.value==struct.unpack('<I',u.mem_read(0x030070a4,4))[0]
 assert bytes(matrix)==bytes(u.mem_read(0x02000800,48))
 callbacks+=len(native_calls)
report=dict(result='PASS',atomic_delta_rejections=rejections,original_ARM_complete_lists=128,callback_handoffs=callbacks,native_steps=steps,scope='Synthetic callback effects change flags,position,next links; full lists and bitmap match. Callbacks also mutate camera translation; actual game callbacks not ported.')
(root/'visibility-object-callback-matrix-tests.json').write_text(json.dumps(report,indent=2));print(report)
