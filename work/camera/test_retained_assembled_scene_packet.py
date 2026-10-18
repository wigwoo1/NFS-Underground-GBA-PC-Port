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
    d=C.CDLL(str(path));packets=[];errors=[];identities=[];raw_packets={};rebuilt_paths=[]
    d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
    d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
    @Sink
    def receive(context,epoch,ptr,size):
        try:
            packet=C.string_at(ptr,size);header=struct.unpack_from('<8I',packet)
            assert header[0]==0x3150534e and header[2]==size
            identities.append(dict(epoch=epoch,serial=header[4],begin=header[5],end=header[6]));raw_packets[header[4]]=packet
            packets.append(hashlib.sha256(packet).hexdigest());return 1
        except Exception as error:errors.append(repr(error));return 0
    assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
    try:
        assert d.nf_native_scene_sink(receive,None)
        available=missing=palette_reads=history_checks=surface_reads=0
        kept=None;kept_model=None
        if diagnostic:
            d.nf_live_completed_surface_extract.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
            d.nf_live_completed_model_extract.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p]
            d.nf_surface_free.argtypes=[C.c_void_p]
            d.nf_assembly_create.restype=C.c_void_p
            d.nf_assembly_destroy.argtypes=[C.c_void_p]
            d.nf_assembly_model.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t]
            d.nf_assembly_surface.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
            d.nf_assembly_finish.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
            d.nf_scene_packet_free.argtypes=[C.c_void_p]
            d.nf_live_completed_surface_verify.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
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
                        ptr=C.c_void_p();n=C.c_size_t();light=C.c_void_p();ln=C.c_size_t()
                        assert d.nf_live_completed_surface_extract(item['epoch'],item['serial'],item['begin'],item['end'],0,C.byref(ptr),C.byref(n),C.byref(light),C.byref(ln))
                        assert n.value>=12
                        original=raw_packets[item['serial']];directory=[struct.unpack_from('<3I',original,32+i*12) for i in range(5)]
                        sections={tag:original[off:off+length] for tag,off,length in directory}
                        model_ptr=C.c_void_p();model_size=C.c_size_t()
                        assert d.nf_live_completed_model_extract(item['epoch'],item['serial'],item['begin'],item['end'],C.byref(model_ptr),C.byref(model_size))
                        rebuilt_model=C.string_at(model_ptr,model_size.value);assert rebuilt_model==sections[1]
                        if kept_model is None:kept_model=(model_ptr,model_size.value,hashlib.sha256(rebuilt_model).hexdigest())
                        else:d.nf_surface_free(model_ptr)
                        order=struct.unpack_from('<'+'I'*struct.unpack_from('<I',sections[3],4)[0],sections[3],8)
                        world={};lights={};ordinal=0
                        for surface_index in order:
                            if surface_index==0xffffffff:continue
                            pp=C.c_void_p();ss=C.c_size_t();ll=C.c_void_p();ls=C.c_size_t()
                            assert d.nf_live_completed_surface_extract(item['epoch'],item['serial'],item['begin'],item['end'],ordinal,C.byref(pp),C.byref(ss),C.byref(ll),C.byref(ls))
                            world[surface_index]=C.string_at(pp,ss.value);lights[surface_index]=C.string_at(ll,ls.value) if ls.value else bytes(4)
                            d.nf_surface_free(pp);d.nf_surface_free(ll);ordinal+=1
                        rebuilt_world=sections[2][:8]+b''.join(world[i] for i in range(len(world)))
                        rebuilt_light=sections[4][:8]+b''.join(lights[i] for i in range(len(lights)))+sections[4][-32768*4:]
                        assert rebuilt_world==sections[2] and rebuilt_light==sections[4]
                        assembly=d.nf_assembly_create();assert assembly
                        try:
                            for surface_index in order:
                                index=len(world) if surface_index==0xffffffff else surface_index
                                identity=C.create_string_buffer(sections[5][8+index*20:28+index*20])
                                if surface_index==0xffffffff:
                                    assert d.nf_assembly_model(assembly,identity,C.create_string_buffer(rebuilt_model),len(rebuilt_model))
                                else:
                                    surface=world[surface_index];lighting=lights[surface_index]
                                    assert d.nf_assembly_surface(assembly,identity,C.create_string_buffer(surface),len(surface),C.create_string_buffer(lighting),len(lighting))
                            built=C.c_void_p();built_size=C.c_size_t();page=struct.unpack_from('<I',original,28)[0]
                            assert d.nf_assembly_finish(assembly,item['serial'],item['begin'],item['end'],page,C.create_string_buffer(sections[4][-32768*4:]),32768*4,C.byref(built),C.byref(built_size))
                            rebuilt=C.string_at(built,built_size.value);d.nf_scene_packet_free(built)
                        finally:d.nf_assembly_destroy(assembly)
                        assert rebuilt==original
                        target=out/('retained-assembled-scene-'+str(item['serial'])+'.bin')
                        # Keep only two explicit reusable fixture names; no corpus deletion.
                        target=out/('retained-assembled-scene-'+str(available%2)+'.bin');target.write_bytes(rebuilt);rebuilt_paths.append(str(target))
                        surface_reads+=1
                        if kept is None:kept=(ptr,n.value,light,ln.value,hashlib.sha256(C.string_at(ptr,n.value)+C.string_at(light,ln.value)).hexdigest())
                        else:d.nf_surface_free(ptr);d.nf_surface_free(light)
                        for ordinal in range(257):
                            key=(C.c_uint32*3)();colors=C.create_string_buffer(512)
                            if not d.nf_live_palette_draw(item['epoch'],item['serial'],item['begin'],item['end'],ordinal,key,colors):break
                            assert key[0] in [1,2];palette_reads+=1
                        assert ordinal>0
                    else:missing+=1;assert result.raw[:4676]==b'\xcc'*4676
                for item in identities[-2:]:
                    verified=(C.c_uint32*2)()
                    assert d.nf_live_completed_surface_verify(item['epoch'],item['serial'],item['begin'],item['end'],verified)
                    assert verified[0]>0 and verified[0]==verified[1];history_checks+=1
                if len(identities)>2:
                    old=identities[-3];verified=(C.c_uint32*2)(99,99)
                    assert not d.nf_live_completed_surface_verify(old['epoch'],old['serial'],old['begin'],old['end'],verified) and list(verified)==[99,99]
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
            deferred=(C.c_uint32*4)();d.nf_live_deferred_surface_stats(deferred)
            assert deferred[0]>0 and deferred[0]==deferred[1] and deferred[2]==0 and deferred[3]==0
            live_report=dict(rebuilt_packets=available,owned_surface_reads=surface_reads,completed_surface_history_checks=history_checks,deferred_surface_comparisons=list(deferred),retained_surface_comparisons=list(retained),surface_read_audit=list(audit),changed_or_unavailable_ranges=[list(ranges[i:i+3]) for i in range(0,96,3) if ranges[i+2]],palette_draws_read=palette_reads,palette_draws_captured=bank_stats[0],palette_banks_retained=bank_stats[1],palette_bank_failures=bank_stats[2],palette_bank_evictions=bank_stats[3],scenes_with_draw_checks=detail[0],draw_checks_different_from_first=detail[1],first_draw_different_from_builder=detail[2],packet_different_from_first_draw=detail[3],maximum_draw_palette_versions=detail[4],palette_version_overflows=detail[5],palette_captures=palette_stats[0],palette_boundary_checks=palette_stats[1],palette_mismatches=palette_stats[2],palette_snapshots=palette_stats[3],query_candidates=stats[0],native_results_verified=stats[1],rejected=stats[2],attached=stats[3],delivered_evaluable=available,missing=missing)
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
            ptr=C.c_void_p(123);n=C.c_size_t(456);light=C.c_void_p(789);ln=C.c_size_t(987)
            assert not d.nf_live_completed_surface_extract(item['epoch'],item['serial'],item['begin'],item['end'],0,C.byref(ptr),C.byref(n),C.byref(light),C.byref(ln))
            assert (ptr.value,n.value,light.value,ln.value)==(123,456,789,987)
            model_ptr=C.c_void_p(123);model_size=C.c_size_t(456)
            assert not d.nf_live_completed_model_extract(item['epoch'],item['serial'],item['begin'],item['end'],C.byref(model_ptr),C.byref(model_size))
            assert (model_ptr.value,model_size.value)==(123,456)
            model_ptr,model_size,model_digest=kept_model
            assert hashlib.sha256(C.string_at(model_ptr,model_size)).hexdigest()==model_digest
            d.nf_surface_free(model_ptr)
            live_report['caller_owned_model_survives_eviction_and_reset']=True
            ptr,n,light,ln,digest=kept
            assert hashlib.sha256(C.string_at(ptr,n)+C.string_at(light,ln)).hexdigest()==digest
            d.nf_surface_free(ptr);d.nf_surface_free(light)
            live_report['caller_owned_surface_survives_eviction_and_reset']=True
            live_report['old_epoch_rejected_after_reset']=True
            (out/'retained-assembled-scene-packet-tests.json').write_text(json.dumps(live_report,indent=2))
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
report=json.loads((out/'retained-assembled-scene-packet-tests.json').read_text());report.update(result='PASS',scene_packets_compared=len(baseline[0]),packet_hashes_and_final_ram_identical=True,
 scope='Opt-in bridge captures, verifies and retains native visibility matched to scene packets. Original renderer still draws; native visibility is not yet consumed by live rendering or interpolated poses.')
(out/'retained-assembled-scene-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)
