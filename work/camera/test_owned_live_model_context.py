from pathlib import Path
import ctypes as C,json
from owned_motion_pairs import records
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));d.nf_geometry_sources_model.argtypes=[C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_uint),C.c_uint];d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];checks=[]
for file in sorted((p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin')):
 model=next(r for r in records(file.read_bytes())['records'] if r['kind']==3);owned=[C.create_string_buffer(bytes(b),len(b)) for b in model['blocks']];ptr=(C.c_void_p*12)(*[C.addressof(b) for b in owned]);sizes=(C.c_uint*12)(*[len(b) for b in model['blocks']]);d.nf_geometry_sources_reset();assert d.nf_geometry_sources_model(model['context'],ptr,sizes,12);assert d.nf_geometry_sources_close(1)
 n=C.c_size_t();assert d.nf_geometry_sources_read(1,None,0,C.byref(n));out=C.create_string_buffer(n.value);assert d.nf_geometry_sources_read(1,out,n.value,C.byref(n));context=out.raw[20:88];expected=bytearray(68);expected[56:60]=model['blocks'][0][56:60];expected[64:68]=model['blocks'][0][64:68];assert context==expected
 for b in owned:C.memset(b,0,len(b))
 again=C.create_string_buffer(n.value);assert d.nf_geometry_sources_read(1,again,n.value,C.byref(n)) and again.raw==out.raw
 checks.append(file.name)
d.nf_geometry_sources_reset();r=dict(result='PASS_LIVE_MODEL_CONTEXT_PUBLICATION',checks=checks,caller_retirement_safe=True,scope='Live publisher owns canonical context, copies all geometry; full-scene producer integration pending.');(p/'owned-live-model-context.json').write_text(json.dumps(r,indent=2));print(r)
