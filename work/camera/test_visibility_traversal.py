"""Whole-ring native traversal checked at actual original call boundaries."""
from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
data=(root/'visibility-entry-200.bin').read_bytes();size=88+0x48000
before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,size)
d=C.CDLL(str((root/'native_visibility.dll').resolve()));fn=d.nfs_visibility_traverse
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]+[C.c_void_p]*8+[C.c_uint]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
registers=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
reports=[];failure_checked=False
for substitute in (False,True):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
    u.mem_write(0x08000000,rom);u.mem_write(0x02000000,data[88:88+0x40000]);u.mem_write(0x03000000,data[88+0x40000:size])
    for reg,v in zip(registers,before[6:]):u.reg_write(reg,v)
    def word(a):return struct.unpack('<I',u.mem_read(a,4))[0]
    def half(a):return struct.unpack('<H',u.mem_read(a,2))[0]
    pending=[];calls=[]
    def hook(cpu,address,length,context):
        global failure_checked
        if pending and address==pending[0]['return']:
            p=pending.pop()
            for a,value in p['outputs']:assert bytes(cpu.mem_read(a,len(value)))==value,(hex(a),p['descriptor'])
            assert cpu.reg_read(UC_ARM_REG_R0)==p['total']
        if address!=0x03002b74:return
        state=cpu.reg_read(UC_ARM_REG_R0);index=cpu.reg_read(UC_ARM_REG_R1);pointer=cpu.reg_read(UC_ARM_REG_R2);parent=cpu.reg_read(UC_ARM_REG_R3);sp=cpu.reg_read(UC_ARM_REG_SP)
        descriptor=word(state+0x14)+index*48;count=half(descriptor+2);vertices=word(state+0x10)+half(descriptor)*68
        table=word(state+0x60);members=word(state+0x64);initial_index=(word(pointer)-table)//16
        buffers=[C.create_string_buffer(bytes(cpu.mem_read(a,n))) for a,n in [(state,256),(descriptor,48),(vertices,count*68),(word(state+0x54),48),(word(state+0x50),64),(parent,16),(table,320),(members,4096)]]
        s,desc,v,cam,proj,src,q,g=buffers;n=C.c_uint32(initial_index);total=C.c_uint32(word(sp));initial_total=total.value
        args=[s,desc,v,count*68,cam,proj,src,reciprocal,q,g,C.byref(n),C.byref(total),word(sp+4)]
        assert fn(*args)
        outputs=[(state,s.raw[:256]),(table,q.raw[:320]),(members,g.raw[:4096]),(pointer,struct.pack('<I',table+n.value*16))]
        calls.append(dict(descriptor=index,edges=count,inserted=n.value-initial_index))
        if not failure_checked and n.value>initial_index:
            saved=[b.raw for b in buffers];saved_n=n.value;saved_t=total.value
            overflow=bytearray(g.raw[:4096]);overflow[::8]=bytes([7])*512;g.raw=bytes(overflow)+b'\0'
            n.value=initial_index;total.value=initial_total
            guards=(s.raw,q.raw,g.raw,n.value,total.value)
            assert not fn(*args)
            assert (s.raw,q.raw,g.raw,n.value,total.value)==guards
            for b,value in zip(buffers,saved):b.raw=value
            n.value=saved_n;total.value=saved_t;failure_checked=True
        if substitute:
            for a,value in outputs:cpu.mem_write(a,value)
            cpu.reg_write(UC_ARM_REG_R0,total.value);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        else:pending.append(dict(outputs=outputs,total=total.value,descriptor=index,**{'return':cpu.reg_read(UC_ARM_REG_LR)}))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(before[2],after[2],count=2000000)
    assert u.reg_read(UC_ARM_REG_PC)==after[2] and not pending and len(calls)==7
    state=before[4];table=word(state+0x60);members=word(state+0x64)
    for a,n in [(table,112),(members,4096)]:assert bytes(u.mem_read(a,n))==data[size+88+a-0x02000000:size+88+a-0x02000000+n]
    reports.append(dict(native_substitution=substitute,calls=calls,queue_and_membership_exact=True))
assert failure_checked
report=dict(result='PASS',runs=reports,overflow_failure_atomic=True,
            scope='Complete native geometry-ring traversal versus seven real original calls and substituted into original outer builder. Outer queue iteration, linked append and merge remain original in this test; no live renderer integration.')
(root/'visibility-traversal-tests.json').write_text(json.dumps(report,indent=2));print(report)
