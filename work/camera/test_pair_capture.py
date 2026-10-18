"""Capture the actual offset matrix and composed selection sequence."""
from pathlib import Path
import ctypes as C, hashlib, json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work').resolve();out=root/'camera'
corpus=out/'pair-corpus';corpus.mkdir(exist_ok=True)
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
        completed=[]
        if diagnostic:
            d.nf_visibility_pair_capture.argtypes=[C.c_char_p,C.c_uint]
            def arm(index):
                assert d.nf_visibility_pair_capture(str(corpus/f'select-{index:02}.bin').encode(),6)
            arm(0)
        for frame in range(850):
            d.nf_frame(1 | (32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
            if diagnostic and d.nf_visibility_status()==2 and len(completed)<24:
                completed.append(f'select-{len(completed):02}.bin')
                if len(completed)<24:arm(len(completed))
        if diagnostic:
            assert len(completed)==24,len(completed)
            (out/'pair-capture-manifest.json').write_text(json.dumps(completed,indent=2))
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'pair-capture-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
dll=C.CDLL(str(out/'native_visibility.dll'))
fn=dll.nfs_visibility_pair;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
offset_fn=dll.nfs_visibility_offset;offset_fn.argtypes=[C.c_void_p,C.c_void_p]
rom=rom_path.read_bytes();reports=[]
for name in json.loads((out/'pair-capture-manifest.json').read_text()):
    data=(corpus/name).read_bytes();size=88+0x48000
    assert len(data)==size*2
    before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,size)
    assert before[:3]==(0x3151564e,0,0x08002cf2) and after[:3]==(0x3151564e,1,0x08002d92)
    ram=data[88:size];post=data[size+88:]
    def memory(addr,length,source=ram):
        for base,chunk in [(0x02000000,source[:0x40000]),(0x03000000,source[0x40000:]),(0x08000000,rom)]:
            if base<=addr and addr+length<=base+len(chunk):return chunk[addr-base:addr-base+length]
        raise ValueError((hex(addr),length))
    def word(addr):return struct.unpack('<I',memory(addr,4))[0]
    errors=[]
    @Reader
    def read(ctx,addr,dst,length):
        try:C.memmove(dst,memory(addr,length),length);return 1
        except Exception as e:errors.append(str(e));return 0
    sp=before[6+13];matrix_address=word(sp+0x98)
    matrix=(C.c_uint32*12)(*struct.unpack('<12I',memory(matrix_address,48)))
    offset=(C.c_uint32*3)();assert offset_fn(matrix,offset)
    assert bytes(offset)==memory(sp+0x7c,12,post)
    selected=struct.unpack('<H',memory(0x03005d44,2))[0]
    point=(C.c_uint32*4)(word(0x03005dd0),word(0x030000a0),offset[0],offset[2])
    state=C.create_string_buffer(memory(before[4],256));result=(C.c_uint32*2)()
    assert fn(state,selected,point,read,None,result) and not errors
    assert list(result)==[after[6+7],after[6+9]],(name,list(result),after[6+7],after[6+9])
    assert state.raw[:256]==memory(before[4],256,post)
    reports.append(dict(file=name,frame=before[3],scene=before[5],matrix_address=hex(matrix_address),offset=list(offset),selected=selected,pair=list(result)))
report=dict(result='PASS',actual_offset_and_pair_sequences=len(reports),scene_packets_compared=len(baseline[0]),
    packet_hashes_and_final_ewram_iwram_vram_identical=True,all_offset_results_and_state_bytes_exact=True,
    distinct_offsets=len({tuple(r['offset']) for r in reports}),distinct_matrix_addresses=sorted({r['matrix_address'] for r in reports}),
    distinct_pairs=sorted({tuple(r['pair']) for r in reports}),samples=reports,
    scope='Actual 08002CF2..08002D92 captures using original stack-selected matrices. Earlier base recovery, later root branching, intermediate-pose visibility and full-scene live rendering remain unverified.')
(out/'pair-capture-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='samples'})
