from pathlib import Path
import ctypes as C,struct,json
root=Path('work/camera');d=C.CDLL(str((root/'native_surface.dll').resolve()))
class View(C.Structure):_fields_=[('width',C.c_uint32),('height',C.c_uint32),('rect',C.c_int32*4),('uv',C.c_uint32*4),('bounds',C.c_uint16*4),('rgba',C.c_void_p)]
d.nf_billboard_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(View)]
record=struct.pack('<4I4i4I4H',0x3142464e,8,4,0,-3,20,80,90,0,0,8,4,0,240,0,160)+bytes(range(128));buf=C.create_string_buffer(record);v=View();assert d.nf_billboard_view(buf,len(record),C.byref(v));assert (v.width,v.height,list(v.rect),list(v.uv),list(v.bounds))==(8,4,[-3,20,80,90],[0,0,8,4],[0,240,0,160]);assert v.rgba==C.addressof(buf)+56 and C.string_at(v.rgba,128)==record[56:]
bad=[record[:i] for i in range(len(record))]+[record+b'x']
for off,value in [(0,0),(4,0),(4,3),(4,2048),(8,0),(8,1025),(12,1),(24,0xfffffffd),(28,20),(32,0xffffffff),(36,0xffffffff),(40,0),(40,9),(44,0),(44,5)]:
 b=bytearray(record);struct.pack_into('<I',b,off,value);bad.append(bytes(b))
for off,value in [(50,0),(54,0)]:
 b=bytearray(record);struct.pack_into('<H',b,off,value);bad.append(bytes(b))
for b in bad:
 C.memset(C.byref(v),0xa5,C.sizeof(v));before=bytes(v);assert not d.nf_billboard_view(C.create_string_buffer(b),len(b),C.byref(v)) and bytes(v)==before
report=dict(result='PASS',valid_borrowed_view=True,malformed_atomic_rejections=len(bad),scope='NFB1 decoder only; unsupported out-of-texture UV rejected, no live renderer integration.')
(root/'billboard-view-tests.json').write_text(json.dumps(report,indent=2));print(report)
