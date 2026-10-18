"""Capture exact builder input/output and verify read-only instrumentation."""
from pathlib import Path
import ctypes as C, hashlib, json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work').resolve();out=root/'camera'
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
def run(path,diagnostic):
    d=C.CDLL(str(path));packets=[];errors=[]
    d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
    d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
    @Sink
    def receive(context,epoch,ptr,size):
        try:packets.append(hashlib.sha256(C.string_at(ptr,size)).hexdigest());return 1
        except Exception as error:errors.append(repr(error));return 0
    assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
    try:
        assert d.nf_native_scene_sink(receive,None)
        if diagnostic:
            d.nf_visibility_capture.argtypes=[C.c_char_p,C.c_uint]
            assert d.nf_visibility_capture(str(out/'visibility-entry-200.bin').encode(),200)
        for _ in range(850):d.nf_frame(1)
        if diagnostic:
            assert d.nf_visibility_status()==2
            rows=(C.c_uint32*(256*7))()
            d.nf_visibility_writes.argtypes=[C.c_void_p,C.c_uint]
            n=d.nf_visibility_writes(rows,256);assert n<256
            (out/'visibility-later-writes.json').write_text(json.dumps(
                [dict(zip(['frame','pc','scene','offset','size','value','thumb'],list(rows)[i*7:i*7+7])) for i in range(n)],indent=2))
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'visibility-entry-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
data=(out/'visibility-entry-200.bin').read_bytes();size=88+0x48000
assert len(data)==size*2
before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,size)
assert before[:3]==(0x3151564e,0,0x03004c74) and after[:3]==(0x3151564e,1,0x03004d50)
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,length in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(address,length)
u.mem_write(0x08000000,rom_path.read_bytes())
u.mem_write(0x02000000,data[88:88+0x40000]);u.mem_write(0x03000000,data[88+0x40000:size])
registers=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
for reg,value in zip(registers,before[6:]):u.reg_write(reg,value)
u.emu_start(before[2],after[2],count=2000000)
assert u.reg_read(UC_ARM_REG_PC)==after[2]
state=before[4];count=struct.unpack('<H',u.mem_read(state+0xee,2))[0];table=struct.unpack('<I',u.mem_read(state+0x60,4))[0]
expected=data[size+88+(table-0x02000000):size+88+(table-0x02000000)+count*16]
assert bytes(u.mem_read(table,count*16))==expected
expected_iwram=data[size+88+0x40000:]
assert count==struct.unpack_from('<H',expected_iwram,state-0x03000000+0xee)[0]
retained=(out/'visibility-scene-200.bin').read_bytes()
before_draw_differences=[dict(offset=i,builder=a,retained=b) for i,(a,b) in enumerate(zip(expected,retained)) if a!=b]
later_writes=json.loads((out/'visibility-later-writes.json').read_text())
packet=(out/'reference-scene-200.packet').read_bytes();delivery_frame=struct.unpack_from('<I',packet,24)[0]
reconstructed=bytearray(expected);applied=[]
for write in later_writes:
    if write['frame']<=delivery_frame:
        assert write['scene']>before[5]
        start=write['offset'];length=write['size']
        reconstructed[start:start+length]=write['value'].to_bytes(length,'little');applied.append(write)
assert bytes(reconstructed)==retained and applied
changed_offsets={row['offset'] for row in before_draw_differences}
causal=[dict(**write,pc_hex=hex(write['pc'])) for write in applied if write['offset'] in changed_offsets]
u.mem_map(0x05000000,0x1000);u.mem_map(0x06000000,0x20000)
queue_writes=[]
def leaf(cpu,address,length,context):
    if address in (0x03005320,0x030053e8,0x030032f0):cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
def wrote(cpu,access,address,length,value,context):
    queue_writes.append(dict(pc=hex(cpu.reg_read(UC_ARM_REG_PC)),offset=address-table,size=length,value=value))
u.hook_add(UC_HOOK_CODE,leaf)
u.hook_add(UC_HOOK_MEM_WRITE,wrote,begin=table,end=table+count*16-1)
u.reg_write(UC_ARM_REG_SP,0x03007e00);u.reg_write(UC_ARM_REG_R0,state);u.reg_write(UC_ARM_REG_LR,0x03006000)
u.emu_start(0x03004d5c,0x03006000,count=2000000)
assert u.reg_read(UC_ARM_REG_PC)==0x03006000
post_draw=bytes(u.mem_read(table,count*16))
post_draw_differences=[dict(offset=i,actual=a,retained=b) for i,(a,b) in enumerate(zip(post_draw,retained)) if a!=b]
report=dict(result='PASS',builder_ordinal=200,entry_frame=before[3],exit_frame=after[3],queue_entries=count,
            native_scene_serial_at_entry=before[5],
            queue_byte_identical=True,scene_packets_compared=len(baseline[0]),all_packet_hashes_identical=True,
            ewram_iwram_vram_identical_after_850_steps=True,
            builder_vs_retained_differences=before_draw_differences,draw_queue_writes=queue_writes,
            later_snapshot_reconstructed_exactly=True,later_snapshot_scene_serials=sorted({w['scene'] for w in applied}),
            changed_bounds_writers=causal,applied_later_writes=len(applied),
            post_draw_queue_matches_retained=post_draw==retained,post_draw_differences=post_draw_differences,
            scope='Exact original builder input/output replay and read-only capture verification. Not a native visibility implementation.')
(out/'visibility-entry-tests.json').write_text(json.dumps(report,indent=2));print(report)
