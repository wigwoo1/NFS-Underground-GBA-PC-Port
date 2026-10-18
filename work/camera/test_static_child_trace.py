"""Original region22 static child trace; raster and object draw effects excluded."""
from pathlib import Path
import json,struct,sys,ctypes as C
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');f=p/'visibility-overflow-171-wide';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();ew=(f/'ewram.bin').read_bytes();iw=(f/'iwram.bin').read_bytes();cases=[]
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
native=d.nfs_visibility_static_child_record;native.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,Read,C.c_void_p,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);rejections=0
for alpha in (.25,.5,.75):
 m=json.loads((f/f'sample-{alpha}.json').read_text());address=m['state_address'];result=(f/f'result-{alpha}.bin').read_bytes();pose=(f/f'pose-{alpha}.bin').read_bytes();count=struct.unpack_from('<H',result,238)[0]
 matches=[i for i in range(count) if struct.unpack_from('<H',result,256+i*16)[0]==22 and not struct.unpack_from('<H',result,266+i*16)[0]&8];assert len(matches)==1
 qi=matches[0];record=result[256+qi*16:272+qi*16]
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for base,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000),(0x05000000,0x1000),(0x06000000,0x20000),(0x08000000,0x800000)):u.mem_map(base,size)
 u.mem_write(0x02000000,ew);u.mem_write(0x03000000,iw);u.mem_write(0x08000000,rom);u.mem_write(address,result[:256]);u.mem_write(struct.unpack_from('<I',result,84)[0],pose[56:104]);u.mem_write(0x04001000,record)
 calls=[];draws=[];objects=[]
 def hook(cpu,pc,length,ctx):
  if pc==0x030027f0:calls.append(dict(record=list(struct.unpack('<8H',cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16))),caller=cpu.reg_read(UC_ARM_REG_LR)))
  if pc in (0x03000304,0x030032f0):
   draws.append(dict(kind=2 if pc==0x03000304 else 1,source=cpu.reg_read(UC_ARM_REG_R6 if pc==0x03000304 else UC_ARM_REG_R7)))
   cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
  if pc==0x0300220c:objects.append(pc);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 u.reg_write(UC_ARM_REG_R0,address);u.reg_write(UC_ARM_REG_R1,0x04001000);u.reg_write(UC_ARM_REG_R2,0);u.reg_write(UC_ARM_REG_SP,0x0400ff00);u.reg_write(UC_ARM_REG_LR,0x03006000)
 u.emu_start(0x030027f0,0x03006000,count=2000000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 assert not objects
 assert [c['record'][0] for c in calls]==[22,228]
 expected=list(struct.unpack('<8H',record));expected[0]=228
 assert calls[1]['record']==expected and calls[1]['caller']==0x03002ae8
 blobs=[(0x02000000,ew),(0x03000000,iw),(0x08000000,rom)];view_address=struct.unpack_from('<I',result,84)[0];fail_read=False;bad_link=False;bad_chain=False
 @Read
 def reader(ctx,a,out,size):
  if fail_read:return 0
  for base,data in blobs:
   if base<=a and a+size<=base+len(data):
    raw=bytearray(data[a-base:a-base+size]);lo=max(a,view_address);hi=min(a+size,view_address+48)
    if lo<hi:raw[lo-a:hi-a]=pose[56+lo-view_address:56+hi-view_address]
    if bad_link and a==struct.unpack_from('<I',result,20)[0]+22*48:struct.pack_into('<H',raw,6,512)
    if bad_chain and a==struct.unpack_from('<I',result,20)[0]+22*48:raw[18]|=8
    C.memmove(out,bytes(raw),size);return 1
  return 0
 output=C.create_string_buffer(b'X'*16,16)
 assert native(C.create_string_buffer(result[:256]),C.create_string_buffer(record),0,reader,None,reciprocal,output)==1
 assert output.raw==struct.pack('<8H',*expected)
 for mode in ('read','link','chain','second-pass'):
  fail_read=mode=='read';bad_link=mode=='link';bad_chain=mode=='chain';output=C.create_string_buffer(b'X'*16,16)
  status=native(C.create_string_buffer(result[:256]),C.create_string_buffer(record),int(mode=='second-pass'),reader,None,reciprocal,output)
  assert status==(0 if mode=='second-pass' else -1) and output.raw==b'X'*16;rejections+=1
 cases.append(dict(alpha=alpha,queue_index=qi,calls=calls,draws=draws,native_child_exact=True))
report=dict(result='PASS',cases=cases,atomic_rejections=rejections,scope='Original region routine preserves parent record for static child228. Raster leaves skipped; object dispatch absent in these calls. Not full-scene rendering or sampled object eligibility proof.')
(p/'static-child-trace-tests.json').write_text(json.dumps(report,indent=2));print(report)
