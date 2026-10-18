"""Synthetic linked-descriptor fixture derived from an actual builder snapshot.
Only isolated in-memory ROM copies are altered; no source ROM writes.
"""
from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=bytearray(Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes())
data=(root/'visibility-entry-200.bin').read_bytes();record_size=88+0x48000
before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,record_size)
ram=data[88:record_size];state=ram[0x40000+before[4]-0x03000000:0x40000+before[4]-0x03000000+256]
descriptors=struct.unpack_from('<I',state,0x14)[0];table,member=struct.unpack_from('<2I',state,0x60)
queue=ram[table-0x02000000:table-0x02000000+320];root_index=struct.unpack_from('<H',queue)[0]
link_address=descriptors+root_index*48+0x20
assert struct.unpack_from('<H',rom,link_address-0x08000000)[0]==65535
struct.pack_into('<H',rom,link_address-0x08000000,21)
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,bytes(rom));u.mem_write(0x02000000,ram[:0x40000]);u.mem_write(0x03000000,ram[0x40000:])
registers=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
for reg,value in zip(registers,before[6:]):u.reg_write(reg,value)
positive=[]
def hook(cpu,address,length,context):
    parent=cpu.reg_read(UC_ARM_REG_R2);index=struct.unpack('<H',cpu.mem_read(parent,2))[0]
    target=struct.unpack('<H',cpu.mem_read(descriptors+index*48+0x20,2))[0]
    if target!=65535:positive.append((index,target))
u.hook_add(UC_HOOK_CODE,hook,begin=0x0300556c,end=0x0300556c)
u.emu_start(before[2],after[2],count=2000000)
assert u.reg_read(UC_ARM_REG_PC)==after[2] and positive==[(root_index,21)]
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
errors=[]
@Reader
def read(context,address,destination,size):
    for base,blob in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
        if base<=address and address+size<=base+len(blob):
            C.memmove(destination,bytes(blob[address-base:address-base+size]),size);return 1
    errors.append((address,size));return 0
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_build
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
s=C.create_string_buffer(state);q=C.create_string_buffer(queue);g=C.create_string_buffer(ram[member-0x02000000:member-0x02000000+4096])
assert fn(s,q,g,read,None,C.create_string_buffer(bytes(rom[0x627700:0x627700+32768*4]))) and not errors
for address,actual in [(before[4],s.raw[:256]),(table,q.raw[:320]),(member,g.raw[:4096])]:assert actual==bytes(u.mem_read(address,len(actual)))
report=dict(result='PASS',synthetic_fixture=True,positive_original_link_calls=positive,queue_entries=struct.unpack_from('<H',s.raw,0xee)[0],
            state_queue_membership_byte_identical=True,ROM_file_unchanged=True,
            scope='Synthetic root descriptor link to 21 in private memory; positive linked path composed with the full builder. Not evidence of that link in unmodified gameplay.')
(root/'visibility-linked-builder-tests.json').write_text(json.dumps(report,indent=2));print(report)
