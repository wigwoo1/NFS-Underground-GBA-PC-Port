from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_region_geometry
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
cases=edges=failures=surface_vertices=0
for group in json.loads((root/'visibility-builder-coverage.json').read_text())['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();stride=88+0x48000;header=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def memory(addr,n):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+n<=base+len(data):return data[addr-base:addr-base+n]
   raise ValueError((hex(addr),n))
  state=bytearray(memory(header[4],256));table=struct.unpack_from('<I',state,0x60)[0]
  for index in range(struct.unpack_from('<H',state,0xee)[0]):
   record=memory(table+index*16,16);region=struct.unpack_from('<H',record)[0];da=struct.unpack_from('<I',state,0x14)[0]+region*48;descriptor=memory(da,48)
   first,count=struct.unpack_from('<2H',descriptor);va=struct.unpack_from('<I',state,0x10)[0]+first*68;vertices=memory(va,count*68)
   state[0xe2:0xea]=record[2:10];scratchaddr=struct.unpack_from('<I',state,0x68)[0]
   u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:]);u.mem_write(header[4],bytes(state))
   def run(start,regs):
    for reg,val in regs+[(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
    u.emu_start(start,0x03006000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
   run(0x03000d48,[(UC_ARM_REG_R0,header[4]),(UC_ARM_REG_R1,da),(UC_ARM_REG_R2,va),(UC_ARM_REG_R3,count)])
   assert u.reg_read(UC_ARM_REG_R0)==1
   initial=bytes(u.mem_read(scratchaddr,count*52))
   surfaceaddr=struct.unpack_from("<I",state,0x6c)[0];surface_initial=bytes(u.mem_read(surfaceaddr,64*24));stream=C.create_string_buffer(surface_initial)
   queue_flags=struct.unpack_from("<H",record,10)[0]
   u.mem_write(0x03007d00,struct.pack('<I',table+index*16))
   run(0x03001800,[(UC_ARM_REG_R0,header[4]),(UC_ARM_REG_R1,va),(UC_ARM_REG_R2,count),(UC_ARM_REG_R3,da)])
   @Reader
   def read(ctx,addr,dst,n):C.memmove(dst,memory(addr,n),n);return 1
   out=C.create_string_buffer(initial);st=C.create_string_buffer(bytes(state));desc=C.create_string_buffer(descriptor);v=C.create_string_buffer(vertices)
   assert fn(st,desc,v,count,queue_flags,read,None,recip,out,len(initial),stream,64*24)==1
   expected=bytes(u.mem_read(scratchaddr,count*52))
   assert st.raw[:256]==bytes(u.mem_read(header[4],256))
   assert stream.raw[:64*24]==bytes(u.mem_read(surfaceaddr,64*24)),(sample["file"],index,"surface")
   emitted=struct.unpack_from("<H",st.raw,0xf2)[0];surface_vertices+=emitted
   assert out.raw[:len(initial)]==expected,(sample['file'],index,[(i,a,b) for i,(a,b) in enumerate(zip(out.raw,expected)) if a!=b][:12])
   @Reader
   def fail(ctx,addr,dst,n):return 0
   out=C.create_string_buffer(initial);st=C.create_string_buffer(bytes(state));stream=C.create_string_buffer(surface_initial)
   assert fn(st,desc,v,count,queue_flags,fail,None,recip,out,len(initial),stream,64*24)==0 and out.raw[:len(initial)]==initial
   assert st.raw[:256]==state and stream.raw[:64*24]==surface_initial
   if emitted:
    assert fn(st,desc,v,count,queue_flags,read,None,recip,out,len(initial),stream,emitted*24-1)==0
    assert out.raw[:len(initial)]==initial and st.raw[:256]==state and stream.raw[:64*24]==surface_initial
   cases+=1;edges+=count;failures+=1
report=dict(result='PASS',captured_region_rings=cases,wall_edges=edges,surface_vertices=surface_vertices,atomic_failed_reads=failures,scope='Complete original03001800 wall scratch, surface stream and state comparison after original transform. Not live drawing.')
(root/'visibility-region-geometry-tests.json').write_text(json.dumps(report,indent=2));print(report)
