from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'candidate-packet-test.dll').resolve()))
f=d.nf_scene_packet_insert_wall;f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
raw=(p/'order-boundary-140.bin').read_bytes();surface=(p/'candidate-at-publication-140.bin').read_bytes();identity=(C.c_uint32*5)(2,50331840,139937176,37,0)
def sections(b):return {t:b[o:o+n] for t,o,n in (struct.unpack_from('<3I',b,32+i*12) for i in range(5))}
original=sections(raw);count=struct.unpack_from('<I',original[2],4)[0]
out=C.c_void_p();size=C.c_size_t()
assert f(raw,len(raw),surface,len(surface),identity,4,C.byref(out),C.byref(size))
result=C.string_at(out,size.value);d.nf_scene_packet_free(out);s=sections(result)
assert s[1]==original[1] and s[2][8:-len(surface)]==original[2][8:] and s[2][-len(surface):]==surface
order=list(struct.unpack_from('<'+'I'*(count+2),s[3],8));expected=list(struct.unpack_from('<'+'I'*(count+1),original[3],8));expected.insert(4,count);assert order==expected
assert s[4][8:-131076]==original[4][8:-131072] and s[4][-131072:]==original[4][-131072:]
assert s[5][-20:]==original[5][-20:]
for b,surf,n,pos in [(raw,surface,len(surface)-1,4),(raw,surface,len(surface),count+1),(result,surface,len(surface),4)]:
 out=C.c_void_p(123);size=C.c_size_t(456)
 assert not f(b,len(b),surf,n,identity,pos,C.byref(out),C.byref(size)) and out.value==123 and size.value==456
(p/'native-candidate-140.bin').write_bytes(result)
report=dict(result='PASS',insert_position=4,atomic_rejections=3,scope='Single unlit candidate packet composition; anchor supplied by caller, no live insertion policy.')
(p/'candidate-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)
