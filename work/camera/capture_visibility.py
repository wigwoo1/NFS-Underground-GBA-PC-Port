"""Read completed-scene visibility records after emulator stepping returns."""
from pathlib import Path
import ctypes as C, json, struct
root=Path('work').resolve(); out=root/'camera'
d=C.CDLL(str(root/'nfsprobe.dll'))
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_read.argtypes=[C.c_uint32,C.c_int];d.nf_read.restype=C.c_uint32
d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
pending=[]; errors=[]; targets={0,40,200}; reports=[]; camera_history=[]
@Sink
def receive(context,epoch,ptr,size):
    try:
        packet=C.string_at(ptr,size); serial=struct.unpack_from('<I',packet,16)[0]
        if serial in targets:pending.append((serial,packet))
        return 1
    except Exception as error:errors.append(repr(error));return 0
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
    assert d.nf_native_scene_sink(receive,None)
    for frame in range(850):
        d.nf_frame(1)
        camera_address=d.nf_read(0x030000c0+0x54,4)
        camera=struct.pack('<12I',*(d.nf_read(camera_address+i*4,4) for i in range(12)))
        projection_address=d.nf_read(0x030000c0+0x50,4)
        projection=struct.pack('<16I',*(d.nf_read(projection_address+i*4,4) for i in range(16)))
        camera_history.append((frame+1,camera,projection));camera_history=camera_history[-16:]
        if 786<=frame+1<=791:
            for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
                d.nf_dump(str(out/f'visibility-step-{frame+1}-{label}.bin').encode(),address,size)
        for serial,packet in pending:
            assert packet==(out/f'reference-scene-{serial}.packet').read_bytes()
            model_offset=struct.unpack_from('<I',packet,36)[0]
            position=struct.unpack_from('<3d',packet,model_offset+48)
            matching=[(f,m,p) for f,m,p in camera_history if tuple(-v for v in struct.unpack_from('<3i',m,36))==position]
            assert matching and len({m for f,m,p in matching})==1
            (out/f'visibility-scene-{serial}-render-camera.bin').write_bytes(matching[-1][1])
            (out/f'visibility-scene-{serial}-render-projection.bin').write_bytes(matching[-1][2])
            (out/f'visibility-scene-{serial}-camera-history.bin').write_bytes(
                b''.join(struct.pack('<I',f)+m+p for f,m,p in camera_history))
            state=0x030000c0
            table=d.nf_read(state+0x60,4);count=d.nf_read(state+0xee,2)
            assert 0<count<=20 and 0x02000000<=table<0x02040000
            path=out/f'visibility-scene-{serial}.bin'
            d.nf_dump(str(path).encode(),table,count*16)
            for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
                d.nf_dump(str(out/f'visibility-scene-{serial}-{label}.bin').encode(),address,size)
            entries=[]; data=path.read_bytes()
            for i in range(count):
                fields=struct.unpack_from('<8H',data,i*16)
                desc=d.nf_read(state+0x14,4)+fields[0]*48
                source=d.nf_read(state+0x10,4)+d.nf_read(desc,2)*68
                entries.append(dict(index=i,descriptor=hex(desc),source=hex(source),
                                    source_count=d.nf_read(desc+2,2),fields=list(fields)))
            reports.append(dict(scene=serial,packet_byte_identical=True,table=hex(table),entries=entries,
                                read_after_step=frame+1,matching_camera_step=matching[-1][0],
                                camera_already_advanced=camera!=matching[-1][1]))
        pending.clear()
        if len(reports)==len(targets):break
    assert not errors and len(reports)==len(targets)
finally:d.nf_close()
(out/'visibility-capture.json').write_text(json.dumps(dict(scenes=reports,
    scope='Post-step shared queue, not necessarily the completed packet queue: verified scene-200 sample already includes scene-201 writes. Use exact builder capture for coherent visibility input/output. Not recomputed for interpolated poses.'),indent=2))
print([(x['scene'],len(x['entries'])) for x in reports])
