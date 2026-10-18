"""Native consolidation versus original ARM, including actual builder integration."""
from pathlib import Path
import ctypes as C, json, random, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);u.mem_write(0x03000000,rom[0x71b0c:0x77b0c])
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_merge
fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint]
append=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_append
append.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_uint]
edge=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_edge_record
edge.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
insert=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_insert
insert.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
project=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_project
project.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
transform=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_transform
transform.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
r=random.Random(0x5620);merged=0
for case in range(600):
    count=case%21;queue=bytearray(r.randbytes(count*16));groups=bytearray(512*8)
    for i in range(count):
        struct.pack_into('<H',queue,i*16,r.randrange(512))
        if i%3:struct.pack_into('<H',queue,i*16+10,r.randrange(256)&~8)
    for i in range(512):
        n=r.randrange(8) if count else 0;groups[i*8]=n
        for j in range(n):groups[i*8+j+1]=r.randrange(count)
    q=C.create_string_buffer(bytes(queue));g=C.create_string_buffer(bytes(groups))
    assert fn(q,count,g,512)
    u.mem_write(0x02001000,bytes(queue));u.mem_write(0x02002000,bytes(groups))
    u.mem_write(0x02000060,struct.pack('<2I',0x02001000,0x02002000));u.mem_write(0x020000ee,struct.pack('<H',count))
    u.reg_write(UC_ARM_REG_R0,0x02000000);u.reg_write(UC_ARM_REG_SP,0x03007e00);u.reg_write(UC_ARM_REG_LR,0x03006000)
    u.emu_start(0x03005620,0x03006000,count=100000)
    assert u.reg_read(UC_ARM_REG_PC)==0x03006000
    assert bytes(u.mem_read(0x02001000,count*16))==q.raw[:count*16],case
    merged+=q.raw[:count*16]!=queue
# Invalid input after a valid group's mutation must fail atomically.
queue=bytearray(48);struct.pack_into('<H',queue,32,511)
groups=bytearray(4096);groups[:3]=bytes([2,0,1]);groups[511*8]=8
q=C.create_string_buffer(bytes(queue));assert not fn(q,3,C.create_string_buffer(bytes(groups)),512)
assert q.raw[:48]==queue
assert not fn(q,21,C.create_string_buffer(bytes(groups)),512)
# Replace only original merge stage while original scene-200 builder executes.
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
data=(root/'visibility-entry-200.bin').read_bytes();size=88+0x48000
before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,size)
u.mem_write(0x02000000,data[88:88+0x40000]);u.mem_write(0x03000000,data[88+0x40000:size])
registers=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
for reg,v in zip(registers,before[6:]):u.reg_write(reg,v)
replaced=[];append_calls=[];edge_calls=[];insert_calls=[];project_calls=[];transform_calls=[]
def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def replace(cpu,address,length,context):
    state=cpu.reg_read(UC_ARM_REG_R0);count=struct.unpack('<H',cpu.mem_read(state+0xee,2))[0]
    table=word(state+0x60);members=word(state+0x64)
    q=C.create_string_buffer(bytes(cpu.mem_read(table,count*16)));g=C.create_string_buffer(bytes(cpu.mem_read(members,4096)))
    assert fn(q,count,g,512);cpu.mem_write(table,q.raw[:count*16]);replaced.append(count)
    cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
def replace_append(cpu,address,length,context):
    state=cpu.reg_read(UC_ARM_REG_R0);pointer=cpu.reg_read(UC_ARM_REG_R1);source=cpu.reg_read(UC_ARM_REG_R2)
    linked_pointer=cpu.reg_read(UC_ARM_REG_R3);total_pointer=word(cpu.reg_read(UC_ARM_REG_SP))
    table=word(state+0x60);destination=word(pointer);assert (destination-table)%16==0
    n=C.c_uint32((destination-table)//16);total=C.c_uint32(word(total_pointer));linked=C.c_uint32(word(linked_pointer))
    record=bytes(cpu.mem_read(source,16));index=struct.unpack_from('<H',record)[0]
    descriptor=struct.unpack('<H',cpu.mem_read(word(state+0x14)+index*48+32,2))[0]
    viewport=word(word(state+0x50)+4);left=struct.unpack('<H',cpu.mem_read(viewport,2))[0];right=struct.unpack('<H',cpu.mem_read(viewport+8,2))[0]
    q=C.create_string_buffer(bytes(cpu.mem_read(table,320)))
    assert append(q,20,C.byref(n),C.byref(total),C.byref(linked),C.create_string_buffer(record),descriptor,left,right)
    cpu.mem_write(table,q.raw[:320]);cpu.mem_write(pointer,struct.pack('<I',table+n.value*16))
    cpu.mem_write(total_pointer,struct.pack('<I',total.value));cpu.mem_write(linked_pointer,struct.pack('<I',linked.value))
    append_calls.append(descriptor);cpu.reg_write(UC_ARM_REG_R0,descriptor)
    cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,replace,begin=0x03005620,end=0x03005620)
u.hook_add(UC_HOOK_CODE,replace_append,begin=0x0300556c,end=0x0300556c)
def replace_edge(cpu,address,length,context):
    sp=cpu.reg_read(UC_ARM_REG_SP);state=cpu.reg_read(UC_ARM_REG_R9);destination=cpu.reg_read(UC_ARM_REG_R7)
    def h(a):return struct.unpack('<H',cpu.mem_read(a,2))[0]
    p=[cpu.reg_read(reg) for reg in [UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R10,UC_ARM_REG_R8]]
    p += [word(sp+4),h(word(sp+0x10)+0x2e),word(sp+0xc),h(state+0xe2),h(state+0xe4),h(state+0x5c),h(state+0x5e)]
    output=C.create_string_buffer(bytes(cpu.mem_read(destination,16)))
    result=edge(C.create_string_buffer(bytes(cpu.mem_read(word(sp+0x38),16))),(C.c_int32*11)(*p),output)
    assert result>=0;edge_calls.append(result)
    if result:cpu.mem_write(destination,output.raw[:16])
    cpu.reg_write(UC_ARM_REG_PC,0x03002f14 if result else 0x03002f60)
u.hook_add(UC_HOOK_CODE,replace_edge,begin=0x03002e18,end=0x03002e18)
def replace_insert(cpu,address,length,context):
    sp=cpu.reg_read(UC_ARM_REG_SP);state=cpu.reg_read(UC_ARM_REG_R9)
    table=word(state+0x60);destination=cpu.reg_read(UC_ARM_REG_R7);assert (destination-table)%16==0
    next_index=C.c_uint32((destination-table)//16);total=C.c_uint32(word(sp+0x60))
    members=word(state+0x64);groups=C.create_string_buffer(bytes(cpu.mem_read(members,4096)));descriptor=word(sp+0xc)
    assert insert(groups,512,descriptor,20,C.byref(next_index),C.byref(total))
    cpu.mem_write(members,groups.raw[:4096]);cpu.mem_write(sp+0x60,struct.pack('<I',total.value))
    cpu.reg_write(UC_ARM_REG_R7,table+next_index.value*16);insert_calls.append(descriptor)
    cpu.reg_write(UC_ARM_REG_PC,0x03002f60)
u.hook_add(UC_HOOK_CODE,replace_insert,begin=0x03002f14,end=0x03002f14)
def replace_project(cpu,address,length,context):
    sp=cpu.reg_read(UC_ARM_REG_SP);projection=cpu.reg_read(UC_ARM_REG_R2)
    p=[cpu.reg_read(reg) for reg in [UC_ARM_REG_R5,UC_ARM_REG_R10,UC_ARM_REG_R6,UC_ARM_REG_R8]]
    p += [word(projection+0x10),struct.unpack('<h',cpu.mem_read(projection+8,2))[0],word(sp+0x34),word(sp+0x64)]
    output=(C.c_uint32*5)();result=project((C.c_int32*8)(*p),reciprocal,output);assert result>=0
    project_calls.append(result)
    if result==1:
        for reg,value in zip([UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R10,UC_ARM_REG_R8],output):cpu.reg_write(reg,value)
        cpu.reg_write(UC_ARM_REG_R4,p[4]);cpu.mem_write(sp+4,struct.pack('<I',output[4]))
        cpu.mem_write(sp+8,struct.pack('<i',p[5]))
    cpu.reg_write(UC_ARM_REG_PC,{0:0x03002f60,1:0x03002e18,2:0x03002f70}[result])
u.hook_add(UC_HOOK_CODE,replace_project,begin=0x03002d20,end=0x03002d20)
def replace_transform(cpu,address,length,context):
    sp=cpu.reg_read(UC_ARM_REG_SP);source=word(sp+0x10);base=word(sp+0x18)
    successor=source+68 if word(sp)<word(sp+0x14) else base
    points=struct.unpack('<2I',cpu.mem_read(source,8))+struct.unpack('<2I',cpu.mem_read(successor,8))
    matrix=[0]*12
    for index,offset in [(0,0x30),(6,0x2c),(9,0x28),(2,0x24),(8,0x20),(11,0x1c)]:matrix[index]=word(sp+offset)
    output=(C.c_uint32*4)();assert transform((C.c_uint32*4)(*points),(C.c_uint32*12)(*matrix),output)
    for reg,value in zip([UC_ARM_REG_R5,UC_ARM_REG_R10,UC_ARM_REG_R6,UC_ARM_REG_R8],output):cpu.reg_write(reg,value)
    cpu.reg_write(UC_ARM_REG_R2,word(cpu.reg_read(UC_ARM_REG_R9)+0x50))
    transform_calls.append(successor==base);cpu.reg_write(UC_ARM_REG_PC,0x03002d20)
u.hook_add(UC_HOOK_CODE,replace_transform,begin=0x03002c80,end=0x03002c80)
u.emu_start(before[2],after[2],count=2000000)
assert u.reg_read(UC_ARM_REG_PC)==after[2] and replaced==[7],(hex(u.reg_read(UC_ARM_REG_PC)),hex(after[2]),replaced)
state=before[4];table=word(state+0x60);expected=data[size+88+table-0x02000000:size+88+table-0x02000000+112]
assert bytes(u.mem_read(table,112))==expected
assert append_calls
assert edge_calls and any(edge_calls)
assert len(insert_calls)==sum(edge_calls)
assert project_calls and project_calls.count(1)==len(edge_calls)
assert len(transform_calls)==len(project_calls)
members=word(state+0x64)
expected_members=data[size+88+members-0x02000000:size+88+members-0x02000000+4096]
assert bytes(u.mem_read(members,4096))==expected_members
report=dict(result='PASS',original_ARM_cases=600,cases_changing_queue=merged,invalid_input_atomic=True,
            actual_builder_native_stage_replacements=1,actual_builder_queue_byte_identical=True,
            actual_builder_append_calls=len(append_calls),actual_builder_links_added=sum(d!=65535 for d in append_calls),
            actual_builder_edge_calls=len(edge_calls),actual_builder_edges_accepted=sum(edge_calls),
            actual_builder_insert_calls=len(insert_calls),membership_table_byte_identical=True,
            actual_builder_projection_calls=len(project_calls),actual_builder_projected=project_calls.count(1),
            actual_builder_transform_calls=len(transform_calls),actual_builder_closing_edges=sum(transform_calls),
            scope='Native transform, clipping/projection, edge record, membership insertion, linked append and consolidation. Builder orchestration remains original ARM; no live renderer integration.')
(root/'visibility-merge-tests.json').write_text(json.dumps(report,indent=2));print(report)
