"""Capture exact builder input/output and verify read-only instrumentation."""
from pathlib import Path
import ctypes as C, hashlib, json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work').resolve();out=root/'camera'
corpus=out/'selector-corpus';corpus.mkdir(exist_ok=True)
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
            d.nf_visibility_selector_capture.argtypes=[C.c_char_p,C.c_uint]
            def arm(index):
                assert d.nf_visibility_selector_capture(str(corpus/f'select-{index:02}.bin').encode(),30)
            arm(0)
        for frame in range(850):
            d.nf_frame(1 | (32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
            if diagnostic and d.nf_visibility_status()==2 and len(completed)<24:
                completed.append(f'select-{len(completed):02}.bin')
                if len(completed)<24:arm(len(completed))
        if diagnostic:
            assert len(completed)==24,len(completed)
            (out/'selector-capture-manifest.json').write_text(json.dumps(completed,indent=2))
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'selector-capture-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str(out/'native_visibility.dll')).nfs_visibility_select
fn.argtypes=[C.c_void_p,Reader,C.c_void_p,C.c_void_p]
rom=rom_path.read_bytes();reports=[]
for name in json.loads((out/'selector-capture-manifest.json').read_text()):
    data=(corpus/name).read_bytes();size=88+0x48000
    assert len(data)==size*2
    before=struct.unpack_from('<22I',data);after=struct.unpack_from('<22I',data,size)
    assert before[:3]==(0x3151564e,0,0x03000bd0) and after[:3]==(0x3151564e,1,0x03000d44)
    ram=data[88:size];post=data[size+88:]
    def memory(addr,length):
        for base,source in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
            if base<=addr and addr+length<=base+len(source):return source[addr-base:addr-base+length]
        raise ValueError((hex(addr),length))
    errors=[]
    @Reader
    def read(ctx,addr,dst,length):
        try:C.memmove(dst,memory(addr,length),length);return 1
        except Exception as e:errors.append(str(e));return 0
    state=memory(before[4],256);s=C.create_string_buffer(state);result=C.c_uint32()
    assert fn(s,read,None,C.byref(result)) and not errors
    assert result.value==after[6],(name,result.value,after[6])
    assert s.raw[:256]==state
    off=before[4]-0x02000000 if before[4]<0x03000000 else 0x40000+before[4]-0x03000000
    assert post[off:off+256]==state
    reports.append(dict(file=name,frame=before[3],scene=before[5],current=struct.unpack_from('<H',state,0xea)[0],selected=result.value))
report=dict(result='PASS',exact_selector_entry_exit_pairs=len(reports),scene_packets_compared=len(baseline[0]),
    packet_hashes_and_final_ewram_iwram_vram_identical=True,original_and_native_state_unchanged=True,
    selections=sorted({r['selected'] for r in reports}),region_changes=sum(r['current']!=r['selected'] and r['selected']!=65535 for r in reports),
    no_match=sum(r['selected']==65535 for r in reports),samples=reports,
    scope='Actual local-selector entry/exit comparisons during 850 scripted refreshes. Does not verify full selection policy, intermediate poses or live 60fps rendering.')
(out/'selector-capture-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='samples'})
