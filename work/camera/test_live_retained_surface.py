"""Capture the actual offset matrix and composed selection sequence."""
from pathlib import Path
import ctypes as C, hashlib, json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work').resolve();out=root/'camera'
corpus=out/'pipeline-corpus';corpus.mkdir(exist_ok=True)
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
def run(path,diagnostic):
    d=C.CDLL(str(path));packets=[];errors=[];identities=[]
    d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
    d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
    @Sink
    def receive(context,epoch,ptr,size):
        try:
            packet=C.string_at(ptr,size);header=struct.unpack_from('<8I',packet)
            assert header[0]==0x3150534e and header[2]==size
            identities.append(dict(epoch=epoch,serial=header[4],begin=header[5],end=header[6]))
            packets.append(hashlib.sha256(packet).hexdigest());return 1
        except Exception as error:errors.append(repr(error));return 0
    assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
    try:
        assert d.nf_native_scene_sink(receive,None)
        available=missing=palette_reads=0
        if diagnostic:
            d.nf_live_palette_draw.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p]
            d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
            d.nf_live_visibility_evaluate.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
            rom_data=rom_path.read_bytes();rom_buffer=C.create_string_buffer(rom_data)
            assert d.nf_live_visibility_enable(rom_buffer,len(rom_data),16*1024*1024)
            d.nf_live_surface_audit_enable(1)
            C.memset(rom_buffer,0,len(rom_data))
        seen=0
        for frame in range(850):
            d.nf_frame(1 | (32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
            if diagnostic:
                for item in identities[seen:]:
                    result=C.create_string_buffer(b'\xcc'*4676)
                    ok=d.nf_live_visibility_evaluate(item['epoch'],item['serial'],item['begin'],item['end'],result)
                    if ok:
                        available+=1
                        for ordinal in range(257):
                            key=(C.c_uint32*3)();colors=C.create_string_buffer(512)
                            if not d.nf_live_palette_draw(item['epoch'],item['serial'],item['begin'],item['end'],ordinal,key,colors):break
                            assert key[0] in [1,2];palette_reads+=1
                        assert ordinal>0
                    else:missing+=1;assert result.raw[:4676]==b'\xcc'*4676
                seen=len(identities)
        if diagnostic:
            stats=(C.c_uint32*4)();d.nf_live_visibility_stats(stats)
            assert available and stats[3]==available,(available,list(stats))
            palette_stats=(C.c_uint32*4)();d.nf_live_visibility_palette_stats(palette_stats)
            detail=(C.c_uint32*6)();d.nf_live_visibility_palette_detail(detail)
            bank_stats=(C.c_uint32*4)();d.nf_live_palette_bank_stats(bank_stats)
            assert bank_stats[2]==0 and bank_stats[1]==available
            audit=(C.c_uint32*6)();ranges=(C.c_uint32*96)();d.nf_live_surface_audit_stats(audit,ranges)
            retained=(C.c_uint32*4)();d.nf_live_retained_surface_stats(retained)
            assert retained[0]>0 and retained[1]==retained[0] and retained[2]==0 and retained[3]==0
            live_report=dict(retained_surface_comparisons=list(retained),surface_read_audit=list(audit),changed_or_unavailable_ranges=[list(ranges[i:i+3]) for i in range(0,96,3) if ranges[i+2]],palette_draws_read=palette_reads,palette_draws_captured=bank_stats[0],palette_banks_retained=bank_stats[1],palette_bank_failures=bank_stats[2],palette_bank_evictions=bank_stats[3],scenes_with_draw_checks=detail[0],draw_checks_different_from_first=detail[1],first_draw_different_from_builder=detail[2],packet_different_from_first_draw=detail[3],maximum_draw_palette_versions=detail[4],palette_version_overflows=detail[5],palette_captures=palette_stats[0],palette_boundary_checks=palette_stats[1],palette_mismatches=palette_stats[2],palette_snapshots=palette_stats[3],query_candidates=stats[0],native_results_verified=stats[1],rejected=stats[2],attached=stats[3],delivered_evaluable=available,missing=missing)
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'live-visibility-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        if diagnostic:
            item=identities[-1];result=C.create_string_buffer(b'\xcc'*4676)
            d.nf_native_scene_discontinuity()
            assert not d.nf_live_visibility_evaluate(item['epoch'],item['serial'],item['begin'],item['end'],result)
            assert result.raw[:4676]==b'\xcc'*4676
            key=(C.c_uint32*3)(9,9,9);colors=C.create_string_buffer(b'X'*512)
            assert not d.nf_live_palette_draw(item['epoch'],item['serial'],item['begin'],item['end'],0,key,colors)
            assert list(key)==[9,9,9] and colors.raw[:512]==b'X'*512
            live_report['old_epoch_rejected_after_reset']=True
            (out/'live-retained-surface-tests.json').write_text(json.dumps(live_report,indent=2))
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
report=json.loads((out/'live-retained-surface-tests.json').read_text());report.update(result='PASS',scene_packets_compared=len(baseline[0]),packet_hashes_and_final_ram_identical=True,
 scope='Opt-in bridge captures, verifies and retains native visibility matched to scene packets. Original renderer still draws; native visibility is not yet consumed by live rendering or interpolated poses.')
(out/'live-retained-surface-tests.json').write_text(json.dumps(report,indent=2));print(report)
