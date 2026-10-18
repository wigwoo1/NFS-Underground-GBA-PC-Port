from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_region_setup
fn.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
u.hook_add(UC_HOOK_CODE,lambda cpu,addr,size,ctx:cpu.emu_stop() if addr==0x03006000 else None)
coverage=json.loads((root/'visibility-builder-coverage.json').read_text());prepared=hidden=failures=0
for group in coverage['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();stride=88+0x48000;h=struct.unpack_from('<22I',blob);ram=blob[stride+88:]
  def memory(addr,size):
   for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
    if base<=addr and addr+size<=base+len(data):return data[addr-base:addr-base+size]
   raise ValueError((hex(addr),size))
  state=memory(h[4],256);table=struct.unpack_from('<I',state,0x60)[0];count=struct.unpack_from('<H',state,0xee)[0]
  for index in range(count):
   record=memory(table+index*16,16);region=struct.unpack_from('<H',record)[0];da=struct.unpack_from('<I',state,0x14)[0]+region*48
   for hide in [False,True]:
    # Explicit synthetic material descriptor gate; preserve original geometry.
    ma=struct.unpack_from('<I',state,0x1c)[0]
    patch={da+10:0,da+11:0,ma+8:0x40 if hide else 0,ma+9:0}
    def patched(addr,size):
     result=bytearray(memory(addr,size))
     for key,value in patch.items():
      if addr<=key<addr+size:result[key-addr]=value
     return bytes(result)
    u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:])
    for addr,value in patch.items():u.mem_write(addr,bytes([value]))
    projection=struct.unpack_from('<I',state,0x50)[0];vp=struct.unpack('<I',memory(projection+4,4))[0]
    for reg,val in [(UC_ARM_REG_R0,h[4]),(UC_ARM_REG_R1,table+index*16),(UC_ARM_REG_R2,0),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
    u.emu_start(0x030027f0,0x030028c8,count=1000)
    assert u.reg_read(UC_ARM_REG_PC)==(0x03006000 if hide else 0x030028c8)
    reads=[]
    @Reader
    def read(ctx,addr,dst,size):reads.append((addr,size));C.memmove(dst,patched(addr,size),size);return 1
    b=C.create_string_buffer(state);v=C.create_string_buffer(memory(vp,16));d=C.create_string_buffer(b'\xcc'*48);g=(C.c_uint32*2)(0xcccccccc,0xcccccccc)
    original=(b.raw,v.raw,d.raw,bytes(g))
    assert fn(b,C.create_string_buffer(record),read,None,v,d,g)==(0 if hide else 1)
    if hide:assert (b.raw,v.raw,d.raw,bytes(g))==original;hidden+=1
    else:
     assert b.raw[:256]==bytes(u.mem_read(h[4],256)) and v.raw[:16]==bytes(u.mem_read(vp,16))
     assert d.raw[:48]==patched(da,48)
     assert list(g)==[u.reg_read(UC_ARM_REG_R4),u.reg_read(UC_ARM_REG_R10)]
     prepared+=1
    for addr in patch:
     if addr>=0x08000000:u.mem_write(addr,memory(addr,1))
@Reader
def fail(ctx,addr,dst,size):return 0
before=(b.raw,v.raw,d.raw,bytes(g))
assert fn(b,C.create_string_buffer(record),fail,None,v,d,g)==-1 and (b.raw,v.raw,d.raw,bytes(g))==before
report=dict(result='PASS',prepared_region_cases=prepared,material_hidden_cases=hidden,read_failure_atomic=True,
 scope='Original region setup boundary and hidden return with synthetic material flag gates over captured geometry. Projection bounds/state outputs match; leaf drawing and recursive region chains remain unimplemented.')
(root/'visibility-region-setup-tests.json').write_text(json.dumps(report,indent=2));print(report)
