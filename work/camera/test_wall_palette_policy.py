from pathlib import Path
import ctypes as C, json
p=Path(__file__).resolve().parent
d=C.CDLL(str(p/'visibility-probe.dll'))
for name in ('nf_candidate_palette','nf_wall_candidate_palette'):
    getattr(d,name).argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p]
palettes=bytearray(1024);palettes[512]=31
indices=C.create_string_buffer(bytes([0,1,2]))
out=C.create_string_buffer(b'X'*512,512)
assert not d.nf_candidate_palette(indices,3,bytes(palettes),2,out) and out.raw==b'X'*512
assert d.nf_wall_candidate_palette(indices,3,bytes(palettes),2,out) and out.raw==bytes(palettes[:512])
palettes[514]=1
out.raw=b'X'*512
assert not d.nf_wall_candidate_palette(indices,3,bytes(palettes),2,out) and out.raw==b'X'*512
palettes[514]=0;palettes[518]=1
assert d.nf_wall_candidate_palette(indices,3,bytes(palettes),2,out)
out.raw=b'X'*512
assert not d.nf_wall_candidate_palette(indices,0,bytes(palettes),2,out) and out.raw==b'X'*512
report=dict(result='PASS',checks=['generic zero rejection unchanged','wall transparent zero accepted','visible mismatch atomic rejection','unused mismatch accepted','empty input atomic rejection'])
(p/'wall-palette-policy-tests.json').write_text(json.dumps(report,indent=2));print(report)
