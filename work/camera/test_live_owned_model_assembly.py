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
            deferred=(C.c_uint32*4)();d.nf_live_deferred_surface_stats(deferred)
            assert deferred[0]>0 and deferred[0]==deferred[1] and deferred[2]==0 and deferred[3]==0
            plan=(C.c_uint32*5)();d.nf_live_wall_plan_stats(plan)
            assert plan[0]>0 and plan[1]>0 and plan[3]==0 and plan[4]==0
            geometry=(C.c_uint32*5)();d.nf_live_region_geometry_stats(geometry)
            assert geometry[0]>0 and geometry[0]==geometry[1] and geometry[2]==0 and geometry[3]==0 and geometry[4]>0
            links=(C.c_uint32*9)();d.nf_live_region_link_stats(links)
            assert links[0]>0 and links[1]>0 and links[5]==0 and links[6]==0,list(links)
            objects=(C.c_uint32*7)();d.nf_live_object_region_stats(objects)
            assert objects[0]>0 and objects[0]==objects[1] and objects[2]==0
            changed=(C.c_uint32*41)();d.nf_live_object_changed_words(changed)
            distance=(C.c_uint32*5)();d.nf_live_object_distance_stats(distance)
            assert distance[0]>0 and distance[0]==distance[1] and distance[2]==0 and distance[3]==0
            insertion=(C.c_uint32*5)();d.nf_live_object_insert_stats(insertion)
            assert insertion[0]>0 and insertion[0]==insertion[1] and insertion[2]==0 and insertion[3]==0
            visits=(C.c_uint32*7)();d.nf_live_object_visit_stats(visits)
            assert visits[0]>0 and visits[0]==visits[4] and visits[5]==0 and visits[6]==0
            # Fixed route must cover loop-back visits, not only routine entries.
            assert list(visits[:4])==[1801,468,1333,262],list(visits)
            cursor=(C.c_uint32*6)();d.nf_live_object_cursor_stats(cursor)
            assert cursor[0]>0 and cursor[0]==cursor[3] and cursor[1]==1801 and cursor[2]==1801 and cursor[4]==0 and cursor[5]==0,list(cursor)
            sorting=(C.c_uint32*5)();d.nf_live_object_sort_stats(sorting)
            assert sorting[0]==468 and sorting[1]==468 and sorting[2]==0 and sorting[3]==0,list(sorting)
            collection=(C.c_uint32*6)();d.nf_live_object_collector_stats(collection)
            assert list(collection)==[427,1801,262,427,0,0],list(collection)
            effects=(C.c_uint32*7)();d.nf_live_object_callback_effects(effects)
            assert effects[0]==262,list(effects)
            deltas=(C.c_uint32*(32*6))();overflow=C.c_uint32();delta_count=d.nf_live_object_callback_deltas(deltas,C.byref(overflow))
            assert delta_count==4 and overflow.value==0
            replay=(C.c_uint32*4)();d.nf_live_object_replay_stats(replay)
            assert list(replay)==[427,427,0,0],list(replay)
            draw_setup=(C.c_uint32*5)();d.nf_live_object_draw_setup_stats(draw_setup)
            assert draw_setup[0]>194 and draw_setup[0]==draw_setup[1] and draw_setup[2]==0 and draw_setup[3]==0 and draw_setup[4]==194,list(draw_setup)
            visibility=(C.c_uint32*6)();d.nf_live_object_visible_stats(visibility)
            assert visibility[0]==206 and visibility[1]==206 and visibility[2]==0 and visibility[3]==0 and visibility[4]+visibility[5]==206,list(visibility)
            materials=(C.c_uint32*5)();d.nf_live_object_material_stats(materials)
            assert materials[0]==206 and materials[1]==206 and materials[2]==0 and materials[3]==0,list(materials)
            textures=(C.c_uint32*6)();d.nf_live_object_texture_stats(textures)
            assert textures[0]==206 and textures[1]==206 and textures[2]==0 and textures[3]==0 and textures[4]+textures[5]==206,list(textures)
            model_context=(C.c_uint32*6)();d.nf_live_object_model_context_stats(model_context)
            assert model_context[0]==206 and model_context[1]==206 and model_context[2]==0 and model_context[3]==0 and model_context[4]+model_context[5]==206,list(model_context)
            extraction=(C.c_uint32*4)();d.nf_live_native_context_extract_stats(extraction)
            assert extraction[0]==206 and extraction[1]==206 and extraction[2]==0 and extraction[3]==0,list(extraction)
            assembly=(C.c_uint32*3)();d.nf_live_native_model_assembly_stats(assembly)
            assert list(assembly)==[206,206,0],list(assembly)
            guards=(C.c_uint32*2)();d.nf_live_native_context_guard_stats(guards)
            assert list(guards)==[1236,0],list(guards)
            ranges_model=(C.c_uint32*(128*3))();meta_model=(C.c_uint32*2)();totals_model=(C.c_uint64*2)();d.nf_live_model_read_ranges(ranges_model,meta_model,totals_model)
            assert meta_model[0]>0 and meta_model[1]==0 and totals_model[0]>0
            d.nf_live_owned_model_flush.argtypes=[C.c_uint64]
            assert d.nf_live_owned_model_flush(identities[-1]['epoch']^1)==-1
            assert d.nf_live_owned_model_flush(identities[-1]['epoch'])==1
            assert d.nf_live_owned_model_flush(identities[-1]['epoch'])==0
            owned=(C.c_uint32*4)();d.nf_live_owned_model_stats(owned)
            assert list(owned)==[206,206,0,0],list(owned)
            owned_assembly=(C.c_uint32*2)();d.nf_live_owned_model_assembly_stats(owned_assembly)
            assert list(owned_assembly)==[206,0],list(owned_assembly)
            live_report=dict(owned_model_assembly_stats=list(owned_assembly),owned_model_replay_stats=list(owned),model_read_ranges=[list(ranges_model[i*3:i*3+3]) for i in range(meta_model[0])],model_read_totals=list(totals_model),model_read_overflow=meta_model[1],native_context_guard_stats=list(guards),native_model_assembly_stats=list(assembly),native_context_extraction_stats=list(extraction),live_object_model_context_stats=list(model_context),live_object_texture_stats=list(textures),live_object_material_stats=list(materials),live_object_visible_stats=list(visibility),live_object_draw_setup_stats=list(draw_setup),detached_object_replay_stats=list(replay),callback_byte_deltas=[list(deltas[i*6:i*6+6]) for i in range(delta_count)],callback_delta_overflow=overflow.value,live_object_callback_effects=list(effects),live_object_collector_stats=list(collection),live_object_sort_stats=list(sorting),live_object_cursor_stats=list(cursor),live_object_visit_stats=list(visits),live_object_insert_stats=list(insertion),live_object_distance_stats=list(distance),object_changed_word_offsets={hex(i*4):changed[i] for i in range(41) if changed[i]},live_object_region_stats=list(objects),live_region_link_stats=list(links),live_region_geometry_stats=list(geometry),live_wall_plan_stats=list(plan),deferred_surface_comparisons=list(deferred),retained_surface_comparisons=list(retained),surface_read_audit=list(audit),changed_or_unavailable_ranges=[list(ranges[i:i+3]) for i in range(0,96,3) if ranges[i+2]],palette_draws_read=palette_reads,palette_draws_captured=bank_stats[0],palette_banks_retained=bank_stats[1],palette_bank_failures=bank_stats[2],palette_bank_evictions=bank_stats[3],scenes_with_draw_checks=detail[0],draw_checks_different_from_first=detail[1],first_draw_different_from_builder=detail[2],packet_different_from_first_draw=detail[3],maximum_draw_palette_versions=detail[4],palette_version_overflows=detail[5],palette_captures=palette_stats[0],palette_boundary_checks=palette_stats[1],palette_mismatches=palette_stats[2],palette_snapshots=palette_stats[3],query_candidates=stats[0],native_results_verified=stats[1],rejected=stats[2],attached=stats[3],delivered_evaluable=available,missing=missing)
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'live-visibility-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        if diagnostic:
            item=identities[-1];result=C.create_string_buffer(b'\xcc'*4676)
            d.nf_native_scene_discontinuity()
            assert d.nf_live_owned_model_flush(item['epoch'])==-1
            assert not d.nf_live_visibility_evaluate(item['epoch'],item['serial'],item['begin'],item['end'],result)
            assert result.raw[:4676]==b'\xcc'*4676
            key=(C.c_uint32*3)(9,9,9);colors=C.create_string_buffer(b'X'*512)
            assert not d.nf_live_palette_draw(item['epoch'],item['serial'],item['begin'],item['end'],0,key,colors)
            assert list(key)==[9,9,9] and colors.raw[:512]==b'X'*512
            live_report['old_epoch_rejected_after_reset']=True
            (out/'live-owned-model-assembly-tests.json').write_text(json.dumps(live_report,indent=2))
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
report=json.loads((out/'live-owned-model-assembly-tests.json').read_text());report.update(result='PASS',scene_packets_compared=len(baseline[0]),packet_hashes_and_final_ram_identical=True,
 scope='Opt-in bridge captures, verifies and retains native visibility matched to scene packets. Original renderer still draws; native visibility is not yet consumed by live rendering or interpolated poses.')
(out/'live-owned-model-assembly-tests.json').write_text(json.dumps(report,indent=2));print(report)



