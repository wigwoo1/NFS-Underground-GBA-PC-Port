"""Fresh original-input replay: display-owned palette and Mode4 index usage."""
import ctypes as C,csv,json,hashlib,struct
from pathlib import Path
p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
session=json.loads(Path(str(prefix)+'-session.json').read_text(encoding='utf-8-sig'))
audit=json.loads((p/'owned-display-palette-audit.json').read_text())
for name in ('rom','state'):
    assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
wanted={}
for item in audit['frames']:wanted.setdefault(item['refresh'],[]).append(item)
P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'))
d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_live_visibility_enable.argtypes=[P,Z,Z]
d.nf_native_scene_epoch.restype=C.c_uint64
d.nf_layer_queue_row.argtypes=[C.c_uint64,U,U,P,U]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z)
@Sink
def sink(ctx,epoch,data,size):return 1
d.nf_native_scene_sink.argtypes=[Sink,P]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
checks=[]
try:
    rom=Path(session['rom']).read_bytes()
    assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
    assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
    assert d.nf_layer_queue_enable(1)
    epoch=d.nf_native_scene_epoch();size=d.nf_layer_row_size();assert size==100480
    buffer=C.create_string_buffer(size)
    for update,row in enumerate(csv.DictReader(Path(str(prefix)+'-input.csv').open()),1):
        assert int(row['index'])==update-1
        d.nf_frame(int(row['keys']))
        refresh=d.nf_layer_queue_latest()
        if refresh in wanted:
            frames=wanted.pop(refresh)
            owned=[Path(str(prefix)+f"-dense-{item['frame']:02}-owned-hud.bin").read_bytes() for item in frames]
            counts={192:0,223:0};colors={192:set(),223:set()}
            for y in range(160):
                assert d.nf_layer_queue_row(epoch,refresh,y,buffer,size)
                raw=buffer.raw;assert struct.unpack_from('<2I',raw)==(refresh,y)
                palette=raw[128+0x18000:128+0x18000+512]
                assert all(palette==hud[y*34944+32896:y*34944+32896+512] for hud in owned)
                if 24<=y<144:
                    display=struct.unpack_from('<H',raw,8)[0]
                    assert display&7==4
                    page=0xa000 if display&16 else 0
                    indices=raw[128+page+y*240:128+page+(y+1)*240]
                    for index in counts:
                        counts[index]+=indices.count(index)
                        colors[index].add(struct.unpack_from('<H',palette,index*2)[0])
            checks.append(dict(refresh=refresh,frames=[f['frame'] for f in frames],
                               palette_bytes_exact=True,world_index_counts=counts,
                               world_colors_bgr555={i:sorted(c) for i,c in colors.items()}))
        if not wanted:break
    assert not wanted
finally:d.nf_close()
report=dict(result='PASS',original_updates=update,checks=checks,
            scope='Fresh recorded original replay reproduces BG palette bytes for all160 rows/all16 captures; counts192/223 on original displayed Mode4 world rows. Does not attribute pixels to model geometry or prove GPU colors, timing or60fps.')
(p/'original-display-palette-indices-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
