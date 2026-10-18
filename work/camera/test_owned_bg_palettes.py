"""Actual captured palettes, exact refresh guards and independently owned clone."""
import ctypes as C,json,hashlib,struct
from pathlib import Path
p=Path(__file__).resolve().parent
d=C.CDLL(str(p/'owned-bg-palette-test.dll'));P=C.c_void_p
d.nf_layer_snapshot_create.restype=P
d.nf_layer_snapshot_clone.argtypes=[P];d.nf_layer_snapshot_clone.restype=P
d.nf_layer_snapshot_destroy.argtypes=[P];d.nf_layer_snapshot_reset.argtypes=[P]
d.nf_layer_snapshot_add_parts.argtypes=[P,P,P,P,P]
d.nf_layer_snapshot_bg_palettes.argtypes=[P,C.c_uint32,P]
d.nf_layer_snapshot_zero_colors.argtypes=[P,C.c_uint32,P]
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
checks=[]
for frame in range(1,17):
    raw=Path(str(prefix)+f'-dense-{frame:02}-owned-hud.bin').read_bytes()
    assert len(raw)==160*34944
    refresh=struct.unpack_from('<I',raw)[0]
    snapshot=d.nf_layer_snapshot_create();assert snapshot
    expected=b''.join(raw[y*34944+32896:y*34944+32896+512] for y in range(160))
    vram=C.create_string_buffer(0x18000);out=C.create_string_buffer(b'\xa5'*81920,81920)
    clone=None
    try:
        for y in range(160):
            row=C.create_string_buffer(raw[y*34944:(y+1)*34944])
            assert d.nf_layer_snapshot_add_parts(snapshot,row,vram,C.byref(row,32896),C.byref(row,33920))
            if y==158:
                assert not d.nf_layer_snapshot_bg_palettes(snapshot,refresh,out)
                assert out.raw==b'\xa5'*81920
        for owner,target in ((None,refresh),(snapshot,refresh+1)):
            assert not d.nf_layer_snapshot_bg_palettes(owner,target,out)
            assert out.raw==b'\xa5'*81920
        assert not d.nf_layer_snapshot_bg_palettes(snapshot,refresh,None)
        assert d.nf_layer_snapshot_bg_palettes(snapshot,refresh,out) and out.raw==expected
        zero=(C.c_uint16*160)();assert d.nf_layer_snapshot_zero_colors(snapshot,refresh,zero)
        assert all(zero[y]==struct.unpack_from('<H',expected,y*512)[0] for y in range(160))
        clone=d.nf_layer_snapshot_clone(snapshot);assert clone
        assert d.nf_layer_snapshot_reset(snapshot)
        C.memset(out,0xa5,81920)
        assert not d.nf_layer_snapshot_bg_palettes(snapshot,refresh,out) and out.raw==b'\xa5'*81920
        d.nf_layer_snapshot_destroy(snapshot);snapshot=None
        assert d.nf_layer_snapshot_bg_palettes(clone,refresh,out) and out.raw==expected
        checks.append(dict(frame=frame,refresh=refresh,exact_bytes=81920,clone_independent=True,
                           palette_sha256=hashlib.sha256(expected).hexdigest()))
    finally:
        d.nf_layer_snapshot_destroy(snapshot);d.nf_layer_snapshot_destroy(clone)
report=dict(result='PASS',checks=checks,scope='All256 BG colors/all160 rows of16 real captures, clone lifecycle and atomic guards; no GPU integration or60fps proof.')
(p/'owned-bg-palette-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(result='PASS',captures=len(checks),exact_bytes_per_capture=81920)))
