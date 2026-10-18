from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
P=C.c_void_p;U=C.c_uint32;Read=C.CFUNCTYPE(C.c_int,P,U,P,C.c_size_t)
source=bytearray([0,1,127,255]*8);reads=[]
@Read
def read(user,address,out,size):
 reads.append((address,size))
 if address!=0x02001000 or size!=len(source):return 0
 C.memmove(out,bytes(source),size);return 1
fn=d.nf_model_texture_indices_owned;fn.argtypes=[Read,P,P,C.POINTER(P),C.POINTER(U),C.POINTER(U)]
d.nf_scene_packet_free.argtypes=[P]
context=bytearray(68);struct.pack_into('<I',context,52,0x02001000);struct.pack_into('<2H',context,56,3,4)
out=P();width=U();height=U();expected=bytes(source)
assert fn(read,None,bytes(context),C.byref(out),C.byref(width),C.byref(height))
try:
 source[:]=bytes(32);context[:]=bytes(68)
 assert (width.value,height.value)==(8,4) and C.string_at(out,32)==expected
finally:d.nf_scene_packet_free(out)
guards=0
for shift,rows,address in [(11,4,0x02001000),(3,0,0x02001000),(3,1025,0x02001000),(3,4,0xfffffff0),(3,4,0x02002000)]:
 context=bytearray(68);struct.pack_into('<I',context,52,address);struct.pack_into('<2H',context,56,shift,rows)
 out=P(123);width=U(456);height=U(789)
 assert not fn(read,None,bytes(context),C.byref(out),C.byref(width),C.byref(height))
 assert (out.value,width.value,height.value)==(123,456,789);guards+=1
report=dict(result='PASS',owned_indices=32,includes_opaque_zero=True,atomic_rejections=guards,scope='Bounded owned model-index extraction; packet metadata and scanline GPU integration remain pending.')
(p/'model-texture-indices-tests.json').write_text(json.dumps(report,indent=2));print(report)
