"""Original ARM builder on owned sampled scene171; native query seeds only."""
from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
p=Path('work/camera');fixture=p/'visibility-overflow-171'
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
blobs=[(0x02000000,(fixture/'ewram.bin').read_bytes()),(0x03000000,(fixture/'iwram.bin').read_bytes()),(0x08000000,rom)]
def memory(a,n):
 for b,data in blobs:
  if b<=a and a+n<=b+len(data):return data[a-b:a-b+n]
 raise ValueError((hex(a),n))
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Reader
def read(ctx,a,out,n):
 try:C.memmove(out,memory(a,n),n);return 1
 except ValueError:return 0
d=C.CDLL(str((p/'visibility-probe.dll').resolve()))
d.nfs_visibility_select.argtypes=[C.c_void_p,Reader,C.c_void_p,C.c_void_p]
d.nfs_visibility_query.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
d.nfs_visibility_choose_root.argtypes=[C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p,C.c_void_p]
results=[]
for alpha in (.25,.5,.75):
 meta=json.loads((fixture/f'sample-{alpha}.json').read_text());address=meta['state_address'];pose=(fixture/f'pose-{alpha}.bin').read_bytes()
 state=bytearray(memory(address,256));table,groups=struct.unpack_from('<2I',state,0x60);view=struct.unpack_from('<I',state,0x54)[0]
 selected=struct.unpack('<H',memory(0x03005d44,2))[0]
 # Prove recovery branch is unused, so no guessed recovery value affects seed.
 preliminary=bytearray(state);struct.pack_into('<H',preliminary,0xea,selected)
 base=struct.unpack_from('<2i',pose);struct.pack_into('<i',preliminary,0xc0,base[0]>>8);struct.pack_into('<i',preliminary,0xc8,base[1]>>8)
 found=C.c_uint32();assert d.nfs_visibility_select(C.create_string_buffer(bytes(preliminary)),read,None,C.byref(found)) and found.value!=65535
 s=C.create_string_buffer(bytes(state));chosen=C.c_uint32(selected);pair=(C.c_uint32*2)()
 assert d.nfs_visibility_query(s,C.byref(chosen),selected,C.create_string_buffer(pose[:8]),C.create_string_buffer(pose[8:56]),read,None,pair)
 seed=C.create_string_buffer(16);C.memmove(C.addressof(seed)+2,s.raw[0x58:0x60],8)
 assert d.nfs_visibility_choose_root(s,pair,read,None,C.byref(chosen),seed)
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for b,data in blobs:u.mem_map(b,(len(data)+4095)&~4095);u.mem_write(b,data)
 u.mem_write(address,s.raw[:256]);u.mem_write(table,seed.raw[:16]);u.mem_write(view,pose[56:104])
 # Private stack outside retained IWRAM; bounded write audit stops unexpected writes.
 u.mem_map(0x04000000,0x10000)
 writes=[];unexpected=[]
 allowed=[(address,address+256),(table,table+1024),(groups,groups+4096),(0x04000000,0x04010000)]
 def audit(cpu,access,a,n,value,ctx):
  if not any(lo<=a and a+n<=hi for lo,hi in allowed):unexpected.append((a,n));cpu.emu_stop()
  writes.append((a,n))
 u.hook_add(UC_HOOK_MEM_WRITE,audit)
 u.reg_write(UC_ARM_REG_R0,address);u.reg_write(UC_ARM_REG_SP,0x0400ff00);u.reg_write(UC_ARM_REG_LR,0x03006000)
 u.emu_start(0x03004c74,0x03006000,count=2000000)
 assert not unexpected,unexpected
 assert u.reg_read(UC_ARM_REG_PC)==0x03006000,hex(u.reg_read(UC_ARM_REG_PC))
 count=struct.unpack('<H',u.mem_read(address+0xee,2))[0]
 assert count=={.25:14,.5:22,.75:15}[alpha]
 assert table+1024<=groups
 (fixture/f'original-queue-{alpha}.bin').write_bytes(bytes(u.mem_read(table,count*16)))
 actual=bytes(u.mem_read(address,256))+bytes(u.mem_read(table,320))+bytes(u.mem_read(groups,4096))+struct.pack('<I',chosen.value)
 if meta['available']:assert actual==(fixture/f'result-{alpha}.bin').read_bytes(),alpha
 wide_fixture=p/'visibility-overflow-171-wide'
 wide_meta=json.loads((wide_fixture/f'sample-{alpha}.json').read_text())
 assert wide_meta['identity']==meta['identity'] and wide_meta['ram_sha256']==meta['ram_sha256'] and wide_meta['available']
 wide_actual=bytes(u.mem_read(address,256))+bytes(u.mem_read(table,512))+bytes(u.mem_read(groups,4096))+struct.pack('<I',chosen.value)
 expected_wide=(wide_fixture/f'result-{alpha}.bin').read_bytes()
 assert wide_actual==expected_wide,('wide original parity',alpha,[(i,a,b) for i,(a,b) in enumerate(zip(wide_actual,expected_wide)) if a!=b][:30])
 results.append(dict(alpha=alpha,count=count,table=table,groups=groups,queue_write_end=max((a+n-table for a,n in writes if table<=a<table+1024),default=0),control_exact=meta['available'],wide_original_exact=True,recovery_unused=True))
report=dict(result='PASS',samples=results,scope='Original ARM builder with native query/root seed; adjacent results exact. Queue writes guarded to1024 bytes and groups to4096; this does not establish original allocation capacity.')
(p/'visibility-overflow-builder-tests.json').write_text(json.dumps(report,indent=2));print(report)
