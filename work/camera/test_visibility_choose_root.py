from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_choose_root
fn.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);cases=redirects=0
coverage=json.loads((root/'visibility-builder-coverage.json').read_text())
for group in coverage['cases']:
 for sample in group['samples']:
  blob=(root/'visibility-corpus'/sample['file']).read_bytes();header=struct.unpack_from('<22I',blob);ram=blob[88:88+0x48000]
  for pair in [(17,17),(17,22),(65535,22),(22,65535)]:
   for redirect in [65535,19]:
    patch={}
    def memory(address,size):
     for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
      if base<=address and address+size<=base+len(data):
       value=bytearray(data[address-base:address-base+size])
       for key,byte in patch.items():
        if address<=key<address+size:value[key-address]=byte
       return bytes(value)
     raise ValueError((hex(address),size))
    state=memory(header[4],256);table=struct.unpack_from('<I',state,0x60)[0]
    chosen=pair[1] if pair[0]==65535 else pair[0]
    address=struct.unpack_from('<I',state,0x14)[0]+chosen*48+0x22
    patch.update({address+i:b for i,b in enumerate(struct.pack('<H',redirect))})
    u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:])
    u.mem_write(address,struct.pack('<H',redirect));sp=0x03007d00
    u.mem_write(sp+0xa0,struct.pack('<I',table))
    for reg,value in [(UC_ARM_REG_SP,sp),(UC_ARM_REG_R7,pair[0]),(UC_ARM_REG_R9,pair[1]),(UC_ARM_REG_R10,header[4])]:u.reg_write(reg,value)
    u.emu_start(0x08002feb,0x0806c098,count=1000)
    assert u.reg_read(UC_ARM_REG_PC)==0x0806c098
    assert u.reg_read(UC_ARM_REG_R0)==(0x08076780-0x08071e10)//4
    assert u.reg_read(UC_ARM_REG_R1)==header[4]
    errors=[]
    @Reader
    def read(ctx,addr,dst,size):
     try:C.memmove(dst,memory(addr,size),size);return 1
     except Exception as e:errors.append(str(e));return 0
    s=C.create_string_buffer(state);q=C.create_string_buffer(memory(table,16));selected=C.c_uint32(0xcccccccc)
    assert fn(s,(C.c_uint32*2)(*pair),read,None,C.byref(selected),q) and not errors
    assert q.raw[:16]==bytes(u.mem_read(table,16))
    assert selected.value==struct.unpack('<H',u.mem_read(0x03005d44,2))[0]==chosen
    # Restore patched ROM bytes; all mutations are confined to oracle memory.
    if address>=0x08000000:u.mem_write(address,rom[address-0x08000000:address-0x08000000+2])
    cases+=1;redirects+=redirect!=65535
@Reader
def fail(ctx,addr,dst,size):return 0
for pair,reader in [((65535,65535),read),((512,17),read),((17,17),fail)]:
 q=C.create_string_buffer(b'\xcc'*16);selected=C.c_uint32(0xdddddddd)
 assert not fn(s,(C.c_uint32*2)(*pair),reader,None,C.byref(selected),q)
 assert q.raw[:16]==b'\xcc'*16 and selected.value==0xdddddddd
report=dict(result='PASS',original_Thumb_branch_cases=cases,synthetic_redirect_cases=redirects,atomic_failure_cases=3,
 scope='Root choice and redirect compared up to common builder dispatch for 69 captured worlds with explicit region pairs/redirect fixtures. Does not assert these fixtures occurred during gameplay.')
(root/'visibility-choose-root-tests.json').write_text(json.dumps(report,indent=2));print(report)
