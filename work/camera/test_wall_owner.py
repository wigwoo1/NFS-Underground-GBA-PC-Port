from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'native_surface.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_wall_owner.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32)]
state=bytearray(256);table=bytearray(512*48);struct.pack_into('<II',state,16,0x8000,0x2000);fail=False
@Read
def read(ctx,address,out,size):
 data=state if address==0x1000 and size==256 else table if address==0x2000 and size==len(table) else None
 if fail or data is None:return 0
 C.memmove(out,bytes(data),size);return 1
checks=0
def check(source,expected):
 global checks
 out=C.c_uint32(0xcccccccc);result=d.nf_wall_owner(read,None,0x1000,source,C.byref(out));assert result==bool(expected);assert out.value==(expected or 0xcccccccc);checks+=1
struct.pack_into('<HH',table,7*48,10,4)
for i in range(4):check(0x8000+(10+i)*68,0x2000+7*48)
for source in (0x8000+9*68,0x8000+14*68,0x8000+10*68+1):check(source,None)
struct.pack_into('<HH',table,8*48,10,4);check(0x8000+10*68,None)
struct.pack_into('<HH',table,8*48,0,0);fail=True;check(0x8000+10*68,None);fail=False
struct.pack_into('<I',state,20,0xfffffff0);check(0x8000+10*68,None)
report=dict(result='PASS',checks=checks,scope='Unique bounded owner lookup, ambiguity/missing/misaligned/read failure/address overflow atomic rejection; not visibility.')
(p/'wall-owner-tests.json').write_text(json.dumps(report,indent=2));print(report)
