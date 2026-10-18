"""Second road layer world geometry from original event sources; no screen fit."""
import runpy,ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;v=runpy.run_path(str(p/'test_road_material_layer.py'));globals().update({k:v[k] for k in ['d','Read','read','state','descriptor','regs','source','overrides','out']});overrides.clear();overrides[state]=source[:256];overrides[descriptor]=source[256:304];overrides[regs[0]]=source[304:352];overrides[regs[2]]=source[352:360];overrides[0x05000000]=bytes(512) # Geometry-only fixture; palette colors are not tested.
d.nf_extract_road_layer.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint,C.c_void_p,C.c_void_p];d.nf_surface_free.argtypes=[C.c_void_p]
def get(a,n):
 b=(C.c_uint8*n)();assert read(None,a,b,n);return bytes(b)
h=lambda b,o:struct.unpack_from('<H',b,o)[0];s=lambda b,o:struct.unpack_from('<h',b,o)[0];w=lambda b,o:struct.unpack_from('<I',b,o)[0];sw=lambda b,o:struct.unpack_from('<i',b,o)[0]
ptr=C.c_void_p();size=C.c_size_t();assert d.nf_extract_road_layer(read,None,state,descriptor,regs[0],regs[2],1,C.byref(ptr),C.byref(size))
try:asset=C.string_at(ptr,size.value)
finally:d.nf_surface_free(ptr)
st=source[:256];de=source[256:304];uv=source[352:];count,width,height=struct.unpack_from('<3I',asset);assert count==h(de,2);face=bytes(20) if h(de,10)==65535 else get(w(st,28)+h(de,10)*20,20)
vertices=[]
for i in range(count):
 raw=get(w(st,16)+(h(de,0)+i)*68,68);off=bytes(32) if h(raw,42)==65535 else get(w(st,24)+h(raw,42)*32,32)
 expected=(sw(raw,0)+s(off,0),s(raw,58)+s(off,4)+s(face,4),sw(raw,4)+s(off,2));actual=struct.unpack_from('<3d',asset,12+i*24);assert actual==expected,(actual,expected)
 # Original transform loads the same source U/V attributes for both heights.
 expected_uv=(sw(raw,32)/16384+s(uv,4)/(256*width),sw(raw,36)/16384+s(uv,6)/(512*height));assert struct.unpack_from('<2d',asset,12+count*24+i*16)==expected_uv;vertices.append(actual)
for layer in [2,0xffffffff]:
 sentinel=C.c_void_p(123);n=C.c_size_t(456);assert not d.nf_extract_road_layer(read,None,state,descriptor,regs[0],regs[2],layer,C.byref(sentinel),C.byref(n)) and sentinel.value==123 and n.value==456
(out/'road-second-layer-geometry-test.json').write_text(json.dumps(dict(result='PASS',vertices=vertices,width=width,height=height,bytes=len(asset),checks=['all world vertices use recovered alternate height/offset/face fields','all source UV attributes plus actual second animation offsets','invalid layer atomic rejection'],scope='Source extraction component; world projection/clipping/pass command capture/live GPU are not yet verified.'),indent=2));print('PASS second-layer geometry',count,'vertices')
