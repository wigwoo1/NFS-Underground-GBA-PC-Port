from pathlib import Path
import ctypes as C,struct,json
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'candidate-packet-test.dll'))
f=d.nf_scene_packet_insert_road;f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
def sections(raw):return {t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
raw=(p/'object-replay-143-old.bin').read_bytes();original=sections(raw);count=struct.unpack_from('<I',original[2],4)[0]
cases=[]
for region,descriptor in ((16,139890192),(18,139890288)):
 surface=(p/f'road-candidate-143-{region}.bin').read_bytes()
 identity=(C.c_uint32*5)(1,50331840,descriptor,0,0)
 out=C.c_void_p();size=C.c_size_t()
 assert f(raw,len(raw),surface,len(surface),identity,0,C.byref(out),C.byref(size))
 result=C.string_at(out,size.value);d.nf_scene_packet_free(out);s=sections(result)
 assert s[1]==original[1] and s[2][8:-len(surface)]==original[2][8:] and s[2][-len(surface):]==surface
 assert struct.unpack_from('<I',s[3],8)[0]==count and s[3][12:]==original[3][8:]
 assert s[4][8:-131076]==original[4][8:-131072] and s[4][-131072:]==original[4][-131072:]
 assert s[5][-40:-20]==bytes(identity) and s[5][-20:]==original[5][-20:]
 for packet,asset,n,kind in ((raw,surface,len(surface)-1,1),(result,surface,len(surface),1),(raw,surface,len(surface),2)):
  bad_id=(C.c_uint32*5)(kind,50331840,descriptor,0,0);out=C.c_void_p(123);size=C.c_size_t(456)
  assert not f(packet,len(packet),asset,n,bad_id,0,C.byref(out),C.byref(size)) and out.value==123 and size.value==456
 cases.append(dict(region=region,surface_bytes=len(surface),atomic_rejections=3))
report=dict(result='PASS',cases=cases,scope='Road packet structure and ownership; placeholder command0 tests composition, not correct scene insertion order.')
(p/'road-candidate-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)
