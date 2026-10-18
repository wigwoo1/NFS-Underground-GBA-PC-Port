from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
P=C.c_void_p;U=C.c_uint32;Read=C.CFUNCTYPE(C.c_int,P,U,P,C.c_size_t)
state=bytearray(256);descriptor=bytearray(48);material=bytearray(32);animation=bytearray(8)
struct.pack_into('<I',state,0,0x02004000);struct.pack_into('<I',state,32,0x02002000);struct.pack_into('<I',state,72,0x02003000)
struct.pack_into('<H',descriptor,8,1);struct.pack_into('<H',material,0,1);struct.pack_into('<H',material,10,8);struct.pack_into('<H',material,26,3)
packed=bytearray();expected=bytearray()
for y in range(4):
 row=bytes([0,1,127,255,y,y+1,y+2,y+3]);expected.extend(row);packed.extend(row+bytes([99]*8))
regions={0x02000000:state,0x02001000:descriptor,0x02002020:material,0x02003008:animation,0x02004000:packed}
@Read
def read(user,address,out,size):
 data=regions.get(address)
 if data is None or len(data)!=size:return 0
 C.memmove(out,bytes(data),size);return 1
fn=d.nf_road_texture_indices_owned;fn.argtypes=[Read,P,U,U,C.POINTER(P),C.POINTER(U),C.POINTER(U)]
d.nf_surface_free.argtypes=[P]
out=P();w=U();h=U();assert fn(read,None,0x02000000,0x02001000,C.byref(out),C.byref(w),C.byref(h))
try:
 packed[:]=bytes(len(packed));assert (w.value,h.value)==(8,4) and C.string_at(out,32)==bytes(expected)
finally:d.nf_surface_free(out)
guards=0
for shift,rows,base in [(0,8,0x02004000),(3,6,0x02004000),(11,8,0x02004000),(3,0,0x02004000),(3,3,0x02004000),(3,1025,0x02004000),(3,8,0xfffffff0),(3,8,0x02005000)]:
 struct.pack_into('<H',material,26,shift);struct.pack_into('<H',material,10,rows);struct.pack_into('<I',state,0,base)
 out=P(123);w=U(456);h=U(789)
 assert not fn(read,None,0x02000000,0x02001000,C.byref(out),C.byref(w),C.byref(h))
 assert (out.value,w.value,h.value)==(123,456,789);guards+=1
report=dict(result='PASS',owned_indices=32,packed_padding_excluded=True,atomic_rejections=guards,scope='Owned road index extraction only; packet/world GPU connection pending.')
(p/'road-texture-indices-tests.json').write_text(json.dumps(report,indent=2));print(report)
